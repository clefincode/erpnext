# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Certificate(Document):
	def before_submit(self):
		self.validate_repated_certificate()
	
	def validate_repated_certificate(self):
		certs = frappe.get_list(self.doctype , filters = {
			'student_group' : self.student_group,
			'student' : self.student,
			'certificate_structure': self.certificate_structure,
			'docstatus' : 1
		}, fields=["name"], as_list=True)
		if len(certs):
			frappe.throw("You Can Not Add More Than One Certificate For The Same Student ,Student Group and Certificate Structure")
