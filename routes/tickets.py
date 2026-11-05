import logging
import uuid

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from supabase import AuthError, PostgrestAPIError, SupabaseException

from auth_helpers import require_login, require_staff
from supabase_client import get_user_client

# All the ticket pages: list, new ticket, detail/comments, and status updates
tickets_bp = Blueprint("tickets", __name__)
logger = logging.getLogger(__name__)

# Must match the status values listed in AGENTS.md.
TICKET_STATUSES = ["Submitted", "Acknowledged", "In Progress", "Resolved", "Closed"]
TICKET_CATEGORIES = ["Plumbing", "Electrical", "HVAC", "Furniture", "Cleaning", "Other"]
# Only what a ticket row shows (_ticket_row.html), so list pages load less (Req 5.1).
TICKET_LIST_COLUMNS = "id, title, category, location, status, updated_at, profiles(name, username)"

# Messages we flash when something goes wrong
DB_ERROR = "Could not reach the database. Try again in a moment."
LOGIN_EXPIRED = "Your login expired. Log in again."
TICKET_NOT_FOUND = "Ticket not found."


# Their token died, so clear everything and send them back to login
def _expired_login():
    session.clear()
    flash(LOGIN_EXPIRED, "error")
    return redirect(url_for("auth.login"))


# Wrong id, deleted ticket, or one RLS hides from them, all get the same answer
def _ticket_not_found():
    flash(TICKET_NOT_FOUND, "error")
    return redirect(url_for("tickets.list_tickets"))


# Ticket ids are UUIDs. Checking first means a typo in the URL gets
# "Ticket not found" instead of a database error (F-005).
def _is_ticket_id(ticket_id):
    try:
        uuid.UUID(ticket_id)
    except ValueError:
        return False
    return True


def _get_role():
    """Returns the logged-in user's role ("requester" or "staff")."""
    profile = (
        get_user_client()
        .table("profiles")
        .select("role")
        .eq("id", session["user_id"])
        .single()
        .execute()
    )
    return profile.data["role"]


# Shows the new ticket form, refilled with whatever they typed if it failed
def _render_new_ticket(status=200, **form):
    return (
        render_template("new_ticket.html", categories=TICKET_CATEGORIES, form=form),
        status,
    )


@tickets_bp.get("/tickets")
@require_login
def list_tickets():
    # Staff see every ticket, requesters only see their own
    try:
        is_staff = _get_role() == "staff"
        query = (
            get_user_client()
            .table("tickets")
            .select(TICKET_LIST_COLUMNS)
            .order("updated_at", desc=True)
        )
        # RLS should already hide other users' tickets; filter here too so a
        # misconfigured database can't leak them (F-004).
        if not is_staff:
            query = query.eq("created_by", session["user_id"])
        tickets = query.execute().data
    except AuthError:
        return _expired_login()
    except (PostgrestAPIError, SupabaseException):
        logger.exception("Could not load tickets")
        flash(DB_ERROR, "error")
        tickets = []
        is_staff = False
    return render_template("tickets.html", tickets=tickets, is_staff=is_staff)


@tickets_bp.route("/tickets/new", methods=["GET", "POST"])
@require_login
def new_ticket():
    if request.method == "GET":
        return _render_new_ticket()

    # Grab what they typed, title is the only required field
    form = {
        "title": request.form.get("title", "").strip(),
        "description": request.form.get("description", "").strip(),
        "location": request.form.get("location", "").strip(),
        "category": request.form.get("category", ""),
    }
    if not form["title"]:
        flash("Add a title before submitting the ticket.", "error")
        return _render_new_ticket(400, **form)
    # Someone could send a made up category, just blank it out
    if form["category"] not in TICKET_CATEGORIES:
        form["category"] = ""

    try:
        # created_by comes from the session, never the form (the insert policy checks it).
        created = (
            get_user_client()
            .table("tickets")
            .insert(
                {
                    "title": form["title"],
                    "description": form["description"] or None,
                    "location": form["location"] or None,
                    "category": form["category"] or None,
                    "created_by": session["user_id"],
                }
            )
            .execute()
        )
    except AuthError:
        return _expired_login()
    except (PostgrestAPIError, SupabaseException):
        logger.exception("Could not create ticket")
        flash(DB_ERROR, "error")
        return _render_new_ticket(503, **form)
    # Send them straight to the ticket they just made
    flash("Ticket submitted.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=created.data[0]["id"]))


# The POST half of ticket_detail, adds a comment then goes back to the ticket
def _add_comment(ticket_id):
    text = request.form.get("text", "").strip()
    if not text:
        flash("Write a comment before sending it.", "error")
    else:
        try:
            get_user_client().table("comments").insert(
                {
                    "ticket_id": ticket_id,
                    "user_id": session["user_id"],
                    "text": text,
                }
            ).execute()
        except AuthError:
            return _expired_login()
        except (PostgrestAPIError, SupabaseException):
            logger.exception("Could not add comment")
            flash(DB_ERROR, "error")
        else:
            flash("Comment added.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))


@tickets_bp.route("/tickets/<ticket_id>", methods=["GET", "POST"])
@require_login
def ticket_detail(ticket_id):
    if not _is_ticket_id(ticket_id):
        return _ticket_not_found()
    # POST means they're adding a comment, GET just shows the ticket
    if request.method == "POST":
        return _add_comment(ticket_id)

    # Load the ticket, make sure they're allowed to see it, then load its comments
    try:
        client = get_user_client()
        ticket = (
            client.table("tickets")
            .select("*, profiles(name, username)")
            .eq("id", ticket_id)
            .maybe_single()
            .execute()
        )
        is_staff = _get_role() == "staff"
        if (
            ticket is None
            or ticket.data is None
            or (not is_staff and ticket.data["created_by"] != session["user_id"])
        ):
            return _ticket_not_found()
        # role lets the template mark staff replies (any logged-in user can read profiles)
        comments = (
            client.table("comments")
            .select("*, profiles(name, username, role)")
            .eq("ticket_id", ticket_id)
            .order("timestamp")
            .execute()
            .data
        )
    except AuthError:
        return _expired_login()
    except (PostgrestAPIError, SupabaseException):
        logger.exception("Could not load ticket %s", ticket_id)
        return _ticket_not_found()
    return render_template(
        "ticket_detail.html",
        ticket=ticket.data,
        comments=comments,
        is_staff=is_staff,
        statuses=TICKET_STATUSES,
    )


@tickets_bp.post("/tickets/<ticket_id>/status")
@require_staff
def update_ticket_status(ticket_id):
    # Staff only (Req 2.3.1). Only accept one of the real status values
    if not _is_ticket_id(ticket_id):
        return _ticket_not_found()
    status = request.form.get("status", "")
    if status not in TICKET_STATUSES:
        flash("Pick a valid status.", "error")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))
    try:
        updated_rows = (
            get_user_client()
            .table("tickets")
            .update({"status": status})
            .eq("id", ticket_id)
            .execute()
            .data
        )
    except AuthError:
        return _expired_login()
    except (PostgrestAPIError, SupabaseException):
        logger.exception("Could not update status for ticket %s", ticket_id)
        flash(DB_ERROR, "error")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))
    # Supabase sends back the rows it changed. None means no ticket had this id,
    # so don't say the status changed (F-005)
    if not updated_rows:
        return _ticket_not_found()
    flash(f"Status changed to {status}.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))
