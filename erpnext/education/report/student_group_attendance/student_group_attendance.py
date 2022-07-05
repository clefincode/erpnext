# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, cint, getdate, get_first_day, get_last_day, date_diff, add_days
from frappe import msgprint, _
from calendar import monthrange
from erpnext.education.api import get_student_group_students
from erpnext.education.doctype.student_attendance.student_attendance import get_holiday_list
from erpnext.support.doctype.issue.issue import get_holidays

def execute(filters=None):
	if not filters: filters = {}
	
	course_dates = get_course_dates(filters)
	columns = get_columns(filters , course_dates)	
	students = get_student_group_students(filters.get("student_group"),1)
	students_list = get_students_list(students)
	instructors = get_student_group_instructors(filters.get("student_group")) 
	instructors_list = get_instructors_list(instructors)
	attendancer = students_list if filters.type == "Students" else instructors_list

	att_map = get_student_attendance_list(filters.get("student_group"), attendancer) if filters.type == "Students" else get_instructor_attendance_list(filters.get("student_group"))
	data = []
	if filters.type == 'Students':
		for stud in students:
			row = [stud.student, stud.student_name]
			student_status = frappe.db.get_value("Student", stud.student, "enabled")
			total_p = total_a = 0.0

			for day in course_dates:
				status="None"

				if att_map.get(stud.student):
					status = att_map.get(stud.student).get(day.date, "None")
				elif not student_status:
					status = "Inactive"
				else:
					status = "None"

				status_map = {"Present": "P", "Absent": "A", "None": "", "Inactive":"-", "Holiday":"H"}
				row.append(status_map[status])

				if status == "Present":
					total_p += 1
				elif status == "Absent":
					total_a += 1

			row += [total_p, total_a]
			data.append(row)
		return columns, data
	else:
		for ins in instructors:
			row = [ins.instructor,ins.instructor_name]
			total_p = total_a = 0.0
			for day in course_dates:
				status = "None"
				if att_map.get(ins.instructor):
					status = att_map.get(ins.instructor).get(day.date,"None")
				status_map = {"Present": "P", "Absent": "A", "None": "", "Inactive":"-", "Holiday":"H"}
				row.append(status_map[status])
				if status == "Present":
					total_p += 1
				elif status == "Absent":
					total_a += 1

			row += [total_p, total_a]
			data.append(row)
		return columns, data
					
			

def get_course_dates(filters):
	if filters.type == "Instructors":
		return frappe.db.sql('select distinct date from `tabInstructor Attendance` where student_group = %(student_group)s ORDER BY date',filters,as_dict = 1 )
	else:
		return frappe.db.sql('select distinct date from `tabStudent Attendance` where student_group = %(student_group)s ORDER BY date',filters,as_dict = 1 )
	

def get_columns(filters ,course_dates):
	id = "Student" if filters.type == "Students" else "Instructor"
	name = "Student Name" if filters.type == "Students" else "Instructor Name"
	columns = [ _(id) + ":Link/" + id + ":90", _(name) + "::150"]
	for day in course_dates:
		columns.append(str(day.date.day) + "-" + str(day.date.month) + "::60")
	columns += [_("Total Present") + ":Int:95", _("Total Absent") + ":Int:90"]
	return columns

def get_students_list(students):
	student_list = []
	for stud in students:
		student_list.append(stud.student)
	return student_list

def get_instructors_list(instructors):
	instructor_list = []
	for ins in instructors :
		instructor_list.append(ins.instructor)
	return instructor_list

def get_student_attendance_list(student_group, students_list):
	attendance_list = frappe.db.sql('''select student, date, status
		from `tabStudent Attendance` where student_group = %s
		and docstatus = 1
		order by student, date''',
		(student_group), as_dict=1)

	att_map = {}
	students_with_leave_application = get_students_with_leave_application(students_list)
	for d in attendance_list:
		att_map.setdefault(d.student, frappe._dict()).setdefault(d.date, "")

		if students_with_leave_application.get(d.date) and d.student in students_with_leave_application.get(d.date):
			att_map[d.student][d.date] = "Present"
		else:
			att_map[d.student][d.date] = d.status

	return att_map

def get_instructor_attendance_list(student_group):
	attendance_list = frappe.db.sql('''select instructor, date, is_present
		from `tabInstructor Attendance` where student_group = %s
		and docstatus = 1
		order by instructor, date''',
		(student_group), as_dict=1)

	att_map = {}
	for d in attendance_list:
		att_map.setdefault(d.instructor, frappe._dict()).setdefault(d.date, "")
		att_map[d.instructor][d.date] = "Present" if d.is_present else "Absent"
	return att_map

def get_students_with_leave_application(students_list):
	if not students_list: return
	leave_applications = frappe.db.sql("""
		select student, from_date, to_date
		from `tabStudent Leave Application`
		where
			mark_as_present = 1 and docstatus = 1
			and student in %(students)s
		""", {
			"students": students_list,
		}, as_dict=True)
	students_with_leaves= {}
	for application in leave_applications:
		for date in daterange(application.from_date, application.to_date):
			students_with_leaves.setdefault(date, []).append(application.student)

	return students_with_leaves

def daterange(d1, d2):
	import datetime
	return (d1 + datetime.timedelta(days=i) for i in range((d2 - d1).days + 1))

@frappe.whitelist()
def get_attendance_years():
	year_list = frappe.db.sql_list('''select distinct YEAR(date) from `tabStudent Attendance` ORDER BY YEAR(date) DESC''')
	if not year_list:
		year_list = [getdate().year]
	return "\n".join(str(year) for year in year_list)

def get_student_group_instructors(student_group):
	return frappe.get_list('Student Group Instructor' , filters = {'parent':student_group} , fields = ['instructor' , 'instructor_name'])