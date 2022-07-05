# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe.model.document import Document
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.general_ledger import make_reverse_gl_entries

class InstructorInvoice(AccountsController):
	def on_submit(self):
		self.make_instructor_attendance_as_completed()
		self.make_gl_entries()
		match_journal = frappe.db.get_single_value("Education Settings", "matching_income_with_instructor_invoice")
		if match_journal:
			self.create_journal_entry()	

	def validate(self):
		self.validate_completed_instructor_attendance()

	def on_cancel(self):
		self.ignore_linked_doctypes = ('GL Entry', 'Stock Ledger Entry')
		self.make_instructor_attendance_as_submitted()
		make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)
	
	def validate_completed_instructor_attendance(self):
		for i,d in enumerate(self.instructor_attendance) : 
			invoiced =  frappe.db.get_value('Instructor Attendance' , d.instructor_attendance_name,'invoiced')
			if invoiced == 1 :
				frappe.throw('row {0} is linked with a Completed Instructor Attendance'.format(i))

	def make_instructor_attendance_as_completed(self):
		for d in self.instructor_attendance:
			frappe.db.set_value('Instructor Attendance',d.instructor_attendance_name ,'invoiced' , 1 )
	
	def make_instructor_attendance_as_submitted(self):
		for d in self.instructor_attendance:
			frappe.db.set_value('Instructor Attendance',d.instructor_attendance_name ,'invoiced' , 0 )	

	def make_gl_entries(self):
		debit_account , credit_account = frappe.db.get_value('Company' , self.company,['instructor_salary_account','instructor_account'])
		cost_center = frappe.db.get_value("Student Group" , self.student_group , 'cost_center')
		expense_gl_entry = self.get_gl_dict({
			"account": debit_account,
			"against": self.employee,
			"debit": self.grand_total,
			"debit_in_account_currency": self.grand_total,
			"cost_center": cost_center
		}, item=self)

		instructor_gl_entries =  self.get_gl_dict({
			"account": credit_account,
			"party_type": "Employee",
			"against": debit_account,
			"party": self.employee,
			"credit": self.grand_total,
			"credit_in_account_currency": self.grand_total,
			"against_voucher": self.name,
			"against_voucher_type": "Instructor Invoice",
			"cost_center": cost_center
		}, item=self)


		from erpnext.accounts.general_ledger import make_gl_entries
		make_gl_entries([instructor_gl_entries, expense_gl_entry], cancel=(self.docstatus == 2),
			update_outstanding="Yes", merge_entries=False)

			
	@frappe.whitelist()
	def get_instructor_attendance(self):
		self.instructor_attendance = []
		atts = frappe.db.get_list('Instructor Attendance' , 
		filters = {
			"invoiced" : 0,
			"is_present" : 1,
			"docstatus" : 1,
			"instructor" : self.instructor,
			"student_group" : self.student_group
		},
		fields = ['instructor' , 'date' , 'time_in' , 'time_out' , 'count_of_hours' , 'name as instructor_attendance_name'] , 
		order_by = 'date')
		sum = 0 
		for att in atts :
			# we can but att because the attribute names in the same
			self.append('instructor_attendance' , att)
			sum += flt(att.count_of_hours)
		self.total_count_hour = sum

	def create_journal_entry(self):
		filters = {
			"cost_center": self.cost_center
		}
		val = frappe.db.sql("""
		select sum(gl.credit) - sum(gl.debit) val from `tabGL Entry` gl
		join `tabAccount` acc on acc.name = gl.account
		where gl.cost_center = %(cost_center)s
		and gl.docstatus = 1 and acc.root_type = 'Income'
		""", values = filters, as_dict = 1)[0].val or 0 
		sg_hours = frappe.db.get_value("Student Group", self.student_group, "total_hours")
		val = (flt(val) / flt(sg_hours)) * flt(self.total_count_hour)
		je = frappe.get_doc({
			"doctype": "Journal Entry",
			"posting_date": self.posting_date,
			"company": self.company,
		})
		je.append("accounts", frappe.get_doc({
			"doctype": "Journal Entry Account",
			"account": frappe.db.get_value("Company", self.company, "default_income_account"),
			"cost_center": self.cost_center,
			"debit_in_account_currency":val,
			"credit_in_account_currency":0,
		}))
		je.append("accounts", frappe.get_doc({
			"doctype": "Journal Entry Account",
			"account": frappe.db.get_value("Company", self.company, "default_achieved_income_account"),
			"cost_center": self.cost_center,
			"debit_in_account_currency":0,
			"credit_in_account_currency":val,
		}))
		je.insert()
		je.submit()
		frappe.msgprint(('Journal Entry Records Created - <a href="#Form/Journal Entry/%s" target="_blank">%s</a>')%(je.name,je.name))