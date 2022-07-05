# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date

class StudentInterest(Document):
	@frappe.whitelist()
	def add_communication_log(self, values):
		values.update({'date': frappe.utils.now()})
		salesman = frappe.db.get_value('Salesman',{'erp_user': frappe.session.user}, 'name')
		if not salesman:
			frappe.throw(_("You Cannot Create Comminucation Log Without Salesman User"))
		values.update({'salesman': salesman})
		self.append('communication_log',values)
		self.status = values['new_status']
		if (len(self.communication_log) == 1 or self.salesman_exp_period < frappe.utils.now()) and values["new_status"] not in ["لم يرد", "خارج التغطية"]:
			self.interest_owner = salesman
			self.salesman_start_period = frappe.utils.now()
			duration = frappe.db.get_value("Program", self.program, 'interest_expiry_duration')
			self.salesman_exp_period = frappe.utils.add_days(frappe.utils.now(), duration)
		self.save()

	@frappe.whitelist()
	def validate_duplicate(self):
		l = frappe.get_list('Student Interest', filters={
			'program': self.program,
			'prospective_phone': self.prospective_phone,
			'name': ['!=', self.name],
			'status': ['!=', "تم التسجيل"]
		}, fields = ['name'])
		if l:
			si = """<a href = "#Form/Student Interest/%s" target = "_blank">%s</a> """ %(l[0].name, l[0].name)
			frappe.throw('Can not Make Two Intersts With The Same Program And Prospective Phone {0}'.format(si))
	
	def validate(self):
		self.validate_duplicate()
		self.validate_dates()

	def validate_dates(self):
		if not self.salesman_exp_period:
			self.salesman_exp_period = add_to_date(self.creation, days=-1)
		if not self.salesman_start_period:
			self.salesman_start_period = add_to_date(self.creation, days=-1)


