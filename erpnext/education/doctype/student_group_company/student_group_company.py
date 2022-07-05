# -*- coding: utf-8 -*-
# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt
from erpnext.education.api import get_grade

class StudentGroupCompany(Document):
	def validate(self):
		self.calc_total()
		self.validate_grade_ar()
	def calc_total(self):
		total = 0
		for s in self.students:
			total += flt(s.paid_amount)
		self.total = total
	
	def validate_grade_ar(self):
		for student in self.students:
			student.grade = get_grade(self.grading_scale, (flt(student.mark)/flt(self.maximum_score))*100)
			student.grade_description = frappe.db.get_value("Grading Scale Interval", {"parent": self.grading_scale, "grade_code": student.grade}, "grade_description")

	def on_submit(self):
		for stud in self.students:
			if stud.has_certificate:
				c = frappe.get_doc({
					"doctype": "Certificate",
					"company": self.company,
					"date_from": self.start_date,
					"date_till": self.end_date,
					"student_name": stud.student_ar_name,
					"student_eng_name": stud.student_en_name,
					"gender": stud.gender,
					"certificate_structure": stud.certificate_type,
					"grade_eng": stud.grade_description,
					"grade": stud.grade,
					"total_score": stud.mark,
					"program": self.program,
					"program_name_ar": self.program_ar_name,
					"hours": self.total_hours,
					"student_group_company": self.name
				})
				c.insert()
				c.submit()

