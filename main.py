from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import psycopg2.extras

app = Flask(__name__)
app.secret_key = "ld;clasdkjfl;asdfjas;"

#TODO: ask about how to deal with IDs
#TODO: ask about trigger nesserary

#TODO: The fuck cursor_factory do?
#TODO: ticketandupdates is TERRIFYING, fix it

def getConn():
    connStr = "dbname = 'postgres' user='postgres' password = 'password'"
    conn = psycopg2.connect(connStr)
    return conn


@app.route('/addCustomer', methods=['post'])
def addCustomer():
    ID = request.form['ID']
    name = request.form['name']
    email = request.form['email']

    conn = getConn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cur.execute("set search_path to ticketsystem")
        cur.execute("insert into customer values (%s, %s, %s)", (ID, name, email))
    except psycopg2.DatabaseError as e:
        conn.rollback()
        if e.pgcode == "23505":
            flash("A customer with that ID already exists")
        elif e.pgcode == "22003":
            flash("A customer with that email address already exists")
        elif e.pgcode == "23514":
            flash("Data of an incorrect nature was inputted into a field (check violation)")
        elif e.pgcode == "22003":
            flash("A numeric value is out of range")
        else:
            flash(e.pgcode)
        return redirect(url_for(".home"))
    else:
        conn.commit()
        flash("Customer successfully added")
        return redirect(url_for(".home"))
    finally:
        if not (conn is None):
            conn.close()

#TODO: TEST
@app.route('/addTicket', methods=["post"])
def addTicket():
    ID = request.form['ID']
    problem = request.form['problem']
    status = request.form['status']
    priority = request.form['priority']
    customerid = request.form['customerid']
    productid = request.form['productid']

    conn = getConn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cur.execute("set search_path to ticketsystem")

        cur.execute("insert into ticket values (%s, %s, %s, %s, current_timestamp, %s, %s)",
                    (ID, problem, status, priority, customerid, productid))
        cur.execute("select to_char(loggedtime, 'YYYY MM DD HH24:MI:SS') from ticket where ticketid = %s" % (ID))
    except psycopg2.DatabaseError as e:
        conn.rollback()
        if e.pgcode == "23505":
            flash("A ticket with that ID already exists")
        elif e.pgcode == "23514":
            flash("Data of an incorrect type was inputted into a field")
        elif e.pgcode == "22003":
            flash("A numeric value is out of range")
        elif e.pgcode == "23503":
            flash("Foreign key provide refers to a non-existent entity")
        else:
            flash(e.pgcode)
        return redirect(url_for(".home"))
    else:
        conn.commit()
        timestamp = cur.fetchall()[0][0]
        flash("Ticket was added successfully")
        tickets = [(ID, problem, status, priority, timestamp, customerid, productid)]
        return render_template("showticket.html", tickets=tickets)
    finally:
        if not (conn is None):
            conn.close()


@app.route("/addUpdate", methods=["post"])
def addUpdate():
    ID = request.form["ID"]
    message = request.form["message"]
    ticketid = request.form["ticketid"]
    staffid = request.form["staffid"]
    staffid = None if staffid == "" else staffid

    conn = getConn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cur.execute("set search_path to ticketsystem")
        cur.execute("insert into ticketupdate values (%s, %s, current_timestamp, %s, %s)",
                    (ID, message, ticketid, staffid))
    except psycopg2.DatabaseError as e:
        conn.rollback()
        if e.pgcode == "23505":
            flash("A ticketupdate with that ID already exists")
        elif e.pgcode == "23514":
            flash("Data of an incorrect type was inputted into a field")
        elif e.pgcode == "22003":
            flash("A numeric value is out of range")
        elif e.pgcode == "23503":
            flash("Foreign key provide refers to a non-existent entity")
        else:
            flash(e.pgcode)
        return redirect(url_for(".home"))
    else:
        conn.commit()
        flash("Update successfully added")
        return redirect(url_for(".home"))
    finally:
        if not (conn is None):
            conn.close()


@app.route("/listOpenTickets", methods=["get"])
def listOpenTickets():
    conn = getConn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cur.execute("set search_path to ticketsystem")
        cur.execute("select * from openticketlatestupdate")
    except psycopg2.DatabaseError as e:
        flash(e.pgerror)
        return redirect(url_for(".home"))
    else:
        tickets = cur.fetchall()
        flash("Open Tickets successfully retrieved")
        return render_template("listopentickets.html", tickets=tickets)
    finally:
        if not (conn is None):
            conn.close()


@app.route("/closeTicket", methods=["post"])
def closeTicket():
    ID = request.form["ID"]

    conn = getConn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cur.execute("set search_path to ticketsystem")
        cur.execute("update ticket set status = 'closed' where ticketid = %s", [int(ID)])
    except psycopg2.DatabaseError as e:
        conn.rollback()
        flash(e.pgerror)
        redirect(url_for(".home"))
    else:
        cur.execute("select * from ticket where ticketid = %s", [int(ID)])
        if cur.fetchall() == []:
            conn.rollback()
            flash("A ticket with that ID doesn't exist")
            return redirect(url_for(".home"))

        conn.commit()
        flash("Ticket has been closed successfully")
        return redirect(url_for(".home"))
    finally:
        if not (conn is None):
            conn.close()


@app.route("/listTicketAndUpdates", methods=["get"])
def listTicketAndUpdates():
    ID = request.args["ID"]

    conn = getConn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("set search_path to ticketsystem")
        cur.execute("select * from ticketandupdates(%s)", [int(ID)])
    except psycopg2.DatabaseError as e:
        flash(e.pgerror)
        return redirect(url_for(".home"))
    else:
        lines = cur.fetchall()
        if lines == []:
            conn.rollback()
            flash("A ticket with that ID doesn't exist")
            return redirect(url_for(".home"))
        flash("Update chain retrieved successfully")
        return render_template("listticketandupdates.html", lines=lines)
    finally:
        if not (conn is None):
            conn.close()


@app.route("/listClosedTicketUpdateStatus", methods=["get"])
def listClosedTicketUpdateStatus():
    conn = getConn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cur.execute("set search_path to ticketsystem")
        cur.execute("select * from closedticketupdatestatus")
    except psycopg2.DatabaseError as e:
        flash(e.pgerror)
        return redirect(url_for(".home"))
    else:
        lines = cur.fetchall()
        flash("Closed Ticket Update Status obtained successfully")
        return render_template("listclosedticketupdatestatus.html", lines=lines)
    finally:
        if not (conn is None):
            conn.close()


@app.route("/deleteCustomer", methods=["post"])
def deleteCustomer():
    ID = request.form["ID"]

    conn = getConn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cur.execute("set search_path to ticketsystem")
        cur.execute("delete from customer where customerid = %s", [int(ID)])
    except psycopg2.DatabaseError as e:
        conn.rollback()
        if e.pgcode == "23505":
            flash("A  with that ID already exists")
        elif e.pgcode == "23514":
            flash("Data of an incorrect type was inputted into a field")
        elif e.pgcode == "22003":
            flash("A numeric value is out of range")
        elif e.pgcode == "23503":
            flash("A customer's associated tickets must be deleted first")
        else:
            flash(e.pgcode)
        return redirect(url_for(".home"))
    else:
        if cur.fetchall() == []:
            flash("A customer with that ID doesn't exist")
            return redirect(url_for(".home"))

        conn.commit()
        flash("Customer successfully deleted")
        return redirect(url_for(".home"))
    finally:
        if not (conn is None):
            conn.close()


@app.route('/', methods=["get"])
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug = True)