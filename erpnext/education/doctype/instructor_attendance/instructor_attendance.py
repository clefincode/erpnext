# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import time_diff_in_seconds, flt

class InstructorAttendance(Document):
	def  before_save (self):
		self.validate_duplicate_dates()
	def on_submit(self):
		self.calculate_actual_houres()

	def on_cancel(self):
		self.calculate_actual_houres()

	@frappe.whitelist()
	def get_difference(self):
		return time_diff_in_seconds(self.time_out , self.time_in)/3600

	def calculate_actual_houres(self):
		atts = frappe.get_list("Instructor Attendance",{"student_group": self.student_group , "docstatus": 1 , "is_present ": 1},["count_of_hours"])
		actual_hours = sum(flt(att.count_of_hours) for att in atts)
		frappe.db.set_value("Student Group",self.student_group,"actual_hours" , actual_hours)
	
	def validate_duplicate_dates(self):
		count = frappe.db.count("Instructor Attendance",{
			"instructor": self.instructor,
			"date": self.date,
			"student_group": self.student_group
		})
		if count >= 1:
			frappe.throw(_("Can not create more than one attendance for same instructor,date and student group"))
