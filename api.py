Traceback (most recent call last):
  File "/home/dx2/myenv/lib/python3.10/site-packages/flask/app.py", line 1511, in wsgi_app
    response = self.full_dispatch_request()
  File "/home/dx2/myenv/lib/python3.10/site-packages/flask/app.py", line 919, in full_dispatch_request
    rv = self.handle_user_exception(e)
  File "/home/dx2/myenv/lib/python3.10/site-packages/flask/app.py", line 917, in full_dispatch_request
    rv = self.dispatch_request()
  File "/home/dx2/myenv/lib/python3.10/site-packages/flask/app.py", line 902, in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
  File "/home/dx2/app.py", line 323, in s_status
    limit = get_manual_limit(slot_s) or def_p
  File "/home/dx2/app.py", line 78, in get_manual_limit
    row = conn.execute("SELECT max_limit FROM manual_slot_limits WHERE slot_start=?", (slot_start,)).fetchone()
sqlite3.OperationalError: no such column: max_limit
152.58.37.81 - - [04/Jun/2026 13:08:33] "GET /api/slots_status HTTP/1.1" 500 -