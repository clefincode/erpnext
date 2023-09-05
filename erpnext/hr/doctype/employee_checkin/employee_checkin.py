# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, get_datetime
import datetime
from frappe.utils import cstr
from datetime import time


import pandas as pd


from erpnext.hr.doctype.shift_assignment.shift_assignment import (
	get_actual_start_end_datetime_of_shift,
)
from erpnext.hr.utils import validate_active_employee


class EmployeeCheckin(Document):
	def validate(self):
		validate_active_employee(self.employee)
		self.validate_duplicate_log()
		self.fetch_shift()

	def validate_duplicate_log(self):
		doc = frappe.db.exists('Employee Checkin', {
			'employee': self.employee,
			'time': self.time,
			'name': ['!=', self.name]})
		if doc:
			doc_link = frappe.get_desk_link('Employee Checkin', doc)
			frappe.throw(_('This employee already has a log with the same timestamp.{0}')
				.format("<Br>" + doc_link))

	def fetch_shift(self):
		shift_actual_timings = get_actual_start_end_datetime_of_shift(self.employee, get_datetime(self.time), True)
		if shift_actual_timings[0] and shift_actual_timings[1]:
			if shift_actual_timings[2].shift_type.determine_check_in_and_check_out == 'Strictly based on Log Type in Employee Checkin' and not self.log_type and not self.skip_auto_attendance:
				frappe.throw(_('Log Type is required for check-ins falling in the shift: {0}.').format(shift_actual_timings[2].shift_type.name))
			if not self.attendance:
				self.shift = shift_actual_timings[2].shift_type.name
				self.shift_actual_start = shift_actual_timings[0]
				self.shift_actual_end = shift_actual_timings[1]
				self.shift_start = shift_actual_timings[2].start_datetime
				self.shift_end = shift_actual_timings[2].end_datetime
		else:
			self.shift = None


	def after_insert(self):
		frappe.log_error("error_message", "Save called.  ")
		print("Calling after save")
		""" after insert the checkin Attendance will be created.  """
		data_time_date_day = set_time_date_day(self.time)
		check_previous_att_record = frappe.db.get_value('Attendance', 
			 {
				 "employee" : self.employee,
				 "attendance_date" : data_time_date_day.get("attendance_date")

	 		}, ['name'])
		if check_previous_att_record:
			doc = check_previous_att_record
			frappe.log_error("check_previous_att_record", ".  doc {} ".format(doc))

			print("Yes Attendance is already store. please update the records ")
			if  self.log_type == 'IN':
				print("Here we are updating  data. For in logtype ")
				update_attendance_for_in_record(doc , self.time)
			if  self.log_type == 'OUT':
				print("Here we are storing data. For out logtype ")	
				update_attendance_for_out_record(doc, self.time)	
		else:
			print("Attendance not Found, Please create the new one. ")
			frappe.log_error("check_previous_att_record Not FOund. Attendance. ", ".  check_previous_att_record {} ".format(check_previous_att_record))

			create_attendance_record(self)


def create_attendance_record(obj):

	frappe.log_error("create_attendance_record", "  create_attendance_record.  ")
	data_time_date_day = set_time_date_day(obj.time)
	data_before_entry = compare_time_before_entry(obj.employee , str(data_time_date_day.get("attendance_time")) , data_time_date_day.get("attendance_day_no") )
	doc_attendance = frappe.new_doc('Attendance')
	doc_attendance.employee = obj.employee
	doc_attendance.status = 'Present'
	doc_attendance.attendance_date =  str(data_time_date_day.get("attendance_date"))
	doc_attendance.docstatus  =  0
	doc_attendance.early_exit =  0
	doc_attendance.early_exit_time =  "00:00:00"
	doc_attendance.late_exit =  0
	doc_attendance.late_exit_time =  "00:00:00"
	doc_attendance.late_entry =   data_before_entry.get("late_entry") 
	doc_attendance.late_entry_time =   data_before_entry.get("late_entry_time") 
	doc_attendance.early_entry =   data_before_entry.get("early_entry") 
	doc_attendance.early_entry_time =   data_before_entry.get("early_entry_time") 
	doc_attendance.late_entry_time_hours =   data_before_entry.get("late_entry_time_hours") 
	doc_attendance.early_entry_time_hours =   round(data_before_entry.get("early_entry_time_hours"),2)
	doc_attendance.timein  =  str(data_time_date_day.get("attendance_time"))
	doc_attendance.first_time_in_time  =  str(data_time_date_day.get("attendance_time"))
	doc_attendance.timeout  =   ""
	doc_attendance.attendance_day  =   data_time_date_day.get("day_name")
	doc_attendance.attendance_day_no  =   data_time_date_day.get("attendance_day_no")
	doc_attendance.last_log_type  =  obj.log_type
	doc_attendance.last_update_in_time  =  str(data_time_date_day.get("attendance_time"))	
	doc_attendance.last_update_out_time  =  "00:00:00"
	try:
		doc_attendance.insert(
		ignore_permissions=True, # ignore write permissions during insert
		ignore_links=True, # ignore Link validation in the document
		ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
		ignore_mandatory=True # insert even if mandatory fields are not set
		)
	except Exception as e:
		print ("Process terminate : {}".format(e))
		error_message = frappe.get_traceback()+"\n{}\n{}".format(str(e))
		frappe.log_error(error_message, "Error in Create Attendance.  ")



def update_attendance_for_in_record(doc , time):
	data_time_date_day = set_time_date_day(time)
	doc_attendance = frappe.get_doc('Attendance', doc )
	doc_attendance.timeout  =  str(data_time_date_day.get("attendance_time"))
	doc_attendance.docstatus = 0
	doc_attendance.last_log_type  =  "IN"
	doc_attendance.last_update_in_time  =  str(data_time_date_day.get("attendance_time"))
	doc_attendance.early_exit =   0
	doc_attendance.early_exit_time =  "00:00:00"
	doc_attendance.late_exit =  0
	doc_attendance.late_exit_time =  "00:00:00"
	try:
		doc_attendance.save(
		ignore_permissions=True, # ignore write permissions during insert
		ignore_version=True # do not create a version record
		)
	except Exception as e:
		print ("Process terminate : {}".format(e))
		error_message = frappe.get_traceback()+"\n{}\n{}".format(str(e))
		frappe.log_error(error_message, "Error in Update Attendance.  ")


def update_attendance_for_out_record(doc , time):
	data_time_date_day = set_time_date_day(time)
	doc_attendance = frappe.get_doc('Attendance', doc )
	data_before_exist = compare_time_before_exist(doc_attendance.get("employee") , str(data_time_date_day.get("attendance_time")) , data_time_date_day.get("attendance_day_no") )
	doc_attendance.timeout  =  str(data_time_date_day.get("attendance_time"))
	doc_attendance.docstatus = 0
	doc_attendance.last_log_type  =  "OUT"
	doc_attendance.early_exit = data_before_exist.get("early_exit")
	doc_attendance.late_exit = data_before_exist.get("late_exit")
	doc_attendance.late_exit_time = data_before_exist.get("late_exit_time")
	doc_attendance.early_exit_time = data_before_exist.get("early_exit_time")
	doc_attendance.early_exit_time_hours = data_before_exist.get("early_exit_time_hours")
	doc_attendance.late_exit_time_hours = data_before_exist.get("late_exit_time_hours")
	doc_attendance.last_update_out_time  =  str(data_time_date_day.get("attendance_time"))
	last_worked_hour = 0.0
	if doc_attendance.working_hours:
		print("already working hours. ")
		last_worked_hour = doc_attendance.working_hours
	time_diff = time_different(doc_attendance.timein , doc_attendance.timeout )
	doc_attendance.working_hours  =(float(time_diff) + float(last_worked_hour))
	try:
		doc_attendance.save(
		ignore_permissions=True, # ignore write permissions during insert
		ignore_version=True # do not create a version record
		)
	except Exception as e:
		print ("Process terminate : {}".format(e))
		error_message = frappe.get_traceback()+"\n{}\n{}".format(str(e))
		frappe.log_error(error_message, "Error in Update Attendance.  ")




def set_time_date_day(time):
	data = {}
	a = str(datetime.datetime.strptime(str(time), "%Y-%m-%d %H:%M:%S"))
	d = a.split(" ")
	attendance_date = d[0]

	weedend = pd.Timestamp(attendance_date)
	attendance_day_no = weedend.dayofweek


	new_time = d[1]
	new_hour = new_time.split(":")[0]
	new_minutes = new_time.split(":")[1]
	attendance_time = new_hour +":"+new_minutes+ ":00"


	data = {
		"attendance_date" :attendance_date ,
		"day_name" : weedend.day_name().capitalize(),
		"attendance_day_no" :attendance_day_no ,
		"attendance_time" :attendance_time ,

	}


	return data




def time_different(start_time , end_time):
	from datetime import datetime
	start_time = datetime.strptime(str(start_time), "%H:%M:%S")
	end_time = datetime.strptime(str(end_time), "%H:%M:%S")	
	# get difference
	delta = end_time - start_time
	sec = delta.total_seconds()
	min = sec / 60
	# get difference in hours
	hours = sec / (60 * 60)
	print('difference in hours:', hours)
	hours = round(hours,2)
	return hours






def compare_time_before_entry(employee_id , started_Work_time , weekend_no ):
	data = {
		"early_entry" : 0,
		"late_entry" : 0,
		"early_entry_time" : "",
		"late_entry_time" : "" , 
		"early_entry_time_hours" : 0.0,
		"late_entry_time_hours" : 0.0
	}
	# started_Work_time = time(hour = 12, minute = 10, second = 0)
	# start_Working_shift_time = time(hour = 11, minute = 00, second = 0)


	shift_time_dict = frappe.db.get_value('Employee Shift Timing', {
		'parent' : employee_id,
		'day_no' : str(weekend_no)
		}, ['day_name', 'status' , 'time_in' , 'time_out'], as_dict = 1)

	if shift_time_dict:
		started_Work_time = datetime.datetime.strptime(str(started_Work_time), "%H:%M:%S")
		start_Working_shift_time = datetime.datetime.strptime(str(shift_time_dict.get("time_in")), "%H:%M:%S")
		if started_Work_time > start_Working_shift_time and start_Working_shift_time < started_Work_time :
			float_hours = time_diff_date_type(started_Work_time , start_Working_shift_time)
			late_entry_in_time = float_hours_to_time(float(abs(float_hours)))
			data["early_entry"] = 0
			data["late_entry"] = 1
			data["late_entry_time"] = str(late_entry_in_time)
			data["early_entry_time"] = "00:00:00"
			data["early_entry_time_hours"] = 0.0
			data["late_entry_time_hours"] = abs(float_hours)
		if started_Work_time == start_Working_shift_time and start_Working_shift_time == started_Work_time :

			data["early_entry_time"] = "00:00:00"
			data["late_entry_time"] = "00:00:00"

			data["early_entry"] = 0
			data["late_entry"] = 0
			data["early_entry_time_hours"] = 0.0
			data["late_entry_time_hours"] = 0.0

		if started_Work_time < start_Working_shift_time and start_Working_shift_time > started_Work_time :
			float_hours = time_diff_date_type(started_Work_time , start_Working_shift_time)
			early_entry_time = float_hours_to_time(float(float_hours))
			data["early_entry"] = 1
			data["late_entry"] = 0

			data["early_entry_time"] = str(early_entry_time)
			data["late_entry_time"] = "00:00:00"
			data["early_entry_time_hours"] = float_hours
			data["late_entry_time_hours"] = 0.0
	else:
		frappe.log_error("shift_time_dict", " Shift Not Found " )
	return data


def compare_time_before_exist(employee_id , ended_Work_time , weekend_no):
	data  = {
	"early_exit" : 0,
	"late_exit" : 0,
	"late_exit_time" : "",
	"early_exit_time"  : "",
	"early_exit_time_hours" : 0.0,
	"late_exit_time_hours": 0.0
	}
	shift_time_dict = frappe.db.get_value('Employee Shift Timing', {
		'parent' : employee_id,
		'day_no' : str(weekend_no)
		}, ['day_name', 'status' , 'time_in' , 'time_out'], as_dict = 1)
	if shift_time_dict:
		ended_Working_shift_time = shift_time_dict.get("time_out")
		ended_Work_time = datetime.datetime.strptime(str(ended_Work_time), "%H:%M:%S")
		ended_Working_shift_time = datetime.datetime.strptime(str(ended_Working_shift_time), "%H:%M:%S")

		if ended_Work_time > ended_Working_shift_time and ended_Working_shift_time < ended_Work_time :	
			float_hours = time_diff_date_type(ended_Work_time , ended_Working_shift_time)
			early_exit_time = float_hours_to_time(float(abs(float_hours)))			
			data["early_exit"] = 0
			data["late_exit"]  = 1
			data["late_exit_time"] = str(early_exit_time)
			data["early_exit_time"] = "00:00:00"
			data["early_exit_time_hours"] = 0.0
			data["late_exit_time_hours"] = float(abs(float_hours))
		if ended_Work_time == ended_Working_shift_time and ended_Working_shift_time == ended_Work_time :
			data["early_exit"] = 0
			data["late_exit"]  = 0
			data["late_exit_time"] = "00:00:00"
			data["early_exit_time"] = "00:00:00"
			data["early_exit_time_hours"] = 0.0
			data["late_exit_time_hours"] = 0.0

		if ended_Work_time < ended_Working_shift_time and ended_Working_shift_time > ended_Work_time :
			float_hours = time_diff_date_type(ended_Work_time , ended_Working_shift_time)
			early_exit_time = float_hours_to_time(float(float_hours))
			data["early_exit"] = 1
			data["late_exit"]  = 0
			data["late_exit_time"] = "00:00:00"
			data["early_exit_time"] = str(early_exit_time)
			data["early_exit_time_hours"] = float_hours
			data["late_exit_time_hours"] = 0.0
	else:
		print("shift_time_dict = Record Not Found. ")
	return data



def time_diff_date_type(start_time , end_time ):
	hours  = 0.0
	from datetime import datetime
	print('start_time time_diff_date_type :', start_time)
	print('end_time - time_diff_date_type :', end_time)

	# get difference
	delta = end_time - start_time

	sec = delta.total_seconds()
	print('difference in seconds:', sec)

	min = sec / 60
	print('difference in minutes:', min)

	# get difference in hours
	hours = sec / (60 * 60)
	print('difference in hours:', hours)

	return hours



def float_hours_to_time(float_hours):
	import datetime
	hours = int(float_hours)
	minutes = int((float_hours * 60) % 60)
	seconds = int((float_hours * 3600) % 60)

	time = datetime.time(hours, minutes, seconds)

	return time

# Example usage


@frappe.whitelist()
def add_log_based_on_employee_field(employee_field_value, timestamp, device_id=None, log_type=None, skip_auto_attendance=0, employee_fieldname='attendance_device_id'):
	"""Finds the relevant Employee using the employee field value and creates a Employee Checkin.

	:param employee_field_value: The value to look for in employee field.
	:param timestamp: The timestamp of the Log. Currently expected in the following format as string: '2019-05-08 10:48:08.000000'
	:param device_id: (optional)Location / Device ID. A short string is expected.
	:param log_type: (optional)Direction of the Punch if available (IN/OUT).
	:param skip_auto_attendance: (optional)Skip auto attendance field will be set for this log(0/1).
	:param employee_fieldname: (Default: attendance_device_id)Name of the field in Employee DocType based on which employee lookup will happen.
	"""

	if not employee_field_value or not timestamp:
		frappe.throw(_("'employee_field_value' and 'timestamp' are required."))

	employee = frappe.db.get_values("Employee", {employee_fieldname: employee_field_value}, ["name", "employee_name", employee_fieldname], as_dict=True)
	if employee:
		employee = employee[0]
	else:
		frappe.throw(_("No Employee found for the given employee field value. '{}': {}").format(employee_fieldname,employee_field_value))

	doc = frappe.new_doc("Employee Checkin")
	doc.employee = employee.name
	doc.employee_name = employee.employee_name
	doc.time = timestamp
	doc.device_id = device_id
	doc.log_type = log_type
	if cint(skip_auto_attendance) == 1: doc.skip_auto_attendance = '1'
	doc.insert()

	return doc


def mark_attendance_and_link_log(logs, attendance_status, attendance_date, working_hours=None, late_entry=False, early_exit=False, in_time=None, out_time=None, shift=None):
	"""Creates an attendance and links the attendance to the Employee Checkin.
	Note: If attendance is already present for the given date, the logs are marked as skipped and no exception is thrown.

	:param logs: The List of 'Employee Checkin'.
	:param attendance_status: Attendance status to be marked. One of: (Present, Absent, Half Day, Skip). Note: 'On Leave' is not supported by this function.
	:param attendance_date: Date of the attendance to be created.
	:param working_hours: (optional)Number of working hours for the given date.
	"""
	log_names = [x.name for x in logs]
	employee = logs[0].employee
	if attendance_status == 'Skip':
		frappe.db.sql("""update `tabEmployee Checkin`
			set skip_auto_attendance = %s
			where name in %s""", ('1', log_names))
		return None
	elif attendance_status in ('Present', 'Absent', 'Half Day'):
		employee_doc = frappe.get_doc('Employee', employee)
		if not frappe.db.exists('Attendance', {'employee':employee, 'attendance_date':attendance_date, 'docstatus':('!=', '2')}):
			doc_dict = {
				'doctype': 'Attendance',
				'employee': employee,
				'attendance_date': attendance_date,
				'status': attendance_status,
				'working_hours': working_hours,
				'company': employee_doc.company,
				'shift': shift,
				'late_entry': late_entry,
				'early_exit': early_exit,
				'in_time': in_time,
				'out_time': out_time
			}
			attendance = frappe.get_doc(doc_dict).insert()
			attendance.submit()
			frappe.db.sql("""update `tabEmployee Checkin`
				set attendance = %s
				where name in %s""", (attendance.name, log_names))
			return attendance
		else:
			frappe.db.sql("""update `tabEmployee Checkin`
				set skip_auto_attendance = %s
				where name in %s""", ('1', log_names))
			return None
	else:
		frappe.throw(_('{} is an invalid Attendance Status.').format(attendance_status))


def calculate_working_hours(logs, check_in_out_type, working_hours_calc_type):
	"""Given a set of logs in chronological order calculates the total working hours based on the parameters.
	Zero is returned for all invalid cases.

	:param logs: The List of 'Employee Checkin'.
	:param check_in_out_type: One of: 'Alternating entries as IN and OUT during the same shift', 'Strictly based on Log Type in Employee Checkin'
	:param working_hours_calc_type: One of: 'First Check-in and Last Check-out', 'Every Valid Check-in and Check-out'
	"""
	total_hours = 0
	in_time = out_time = None
	if check_in_out_type == 'Alternating entries as IN and OUT during the same shift':
		in_time = logs[0].time
		if len(logs) >= 2:
			out_time = logs[-1].time
		if working_hours_calc_type == 'First Check-in and Last Check-out':
			# assumption in this case: First log always taken as IN, Last log always taken as OUT
			total_hours = time_diff_in_hours(in_time, logs[-1].time)
		elif working_hours_calc_type == 'Every Valid Check-in and Check-out':
			logs = logs[:]
			while len(logs) >= 2:
				total_hours += time_diff_in_hours(logs[0].time, logs[1].time)
				del logs[:2]

	elif check_in_out_type == 'Strictly based on Log Type in Employee Checkin':
		if working_hours_calc_type == 'First Check-in and Last Check-out':
			first_in_log_index = find_index_in_dict(logs, 'log_type', 'IN')
			first_in_log = logs[first_in_log_index] if first_in_log_index or first_in_log_index == 0 else None
			last_out_log_index = find_index_in_dict(reversed(logs), 'log_type', 'OUT')
			last_out_log = logs[len(logs)-1-last_out_log_index] if last_out_log_index or last_out_log_index == 0 else None
			if first_in_log and last_out_log:
				in_time, out_time = first_in_log.time, last_out_log.time
				total_hours = time_diff_in_hours(in_time, out_time)
		elif working_hours_calc_type == 'Every Valid Check-in and Check-out':
			in_log = out_log = None
			for log in logs:
				if in_log and out_log:
					if not in_time:
						in_time = in_log.time
					out_time = out_log.time
					total_hours += time_diff_in_hours(in_log.time, out_log.time)
					in_log = out_log = None
				if not in_log:
					in_log = log if log.log_type == 'IN'  else None
				elif not out_log:
					out_log = log if log.log_type == 'OUT'  else None
			if in_log and out_log:
				out_time = out_log.time
				total_hours += time_diff_in_hours(in_log.time, out_log.time)
	return total_hours, in_time, out_time

def time_diff_in_hours(start, end):
	return round((end-start).total_seconds() / 3600, 1)

def find_index_in_dict(dict_list, key, value):
	return next((index for (index, d) in enumerate(dict_list) if d[key] == value), None)




