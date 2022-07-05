# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now , flt

class ProgramDisenrollment(Document):
	def validate(self):
		self.validate_total_freezed_balance()

	def validate_total_freezed_balance(self):
		total_new_fees = 0
		for f in self.new_fees:
			total_new_fees += f.transfered_amount
		if total_new_fees > self.total_freezed_balance:
			frappe.throw(_("New Fees Transfered Amount Cannot Be More Than Total Freezed Balance"))

	def on_cancel(self):
		self.mark_student_as_active()
	
	def on_submit(self):
		journal_amount = 0
		has_enrollment_fee = False
		for f in self.fees:
			#delete journal entry of the fees (in case of fees_on_customer)
			jvs = frappe.get_list("Journal Entry Account" , {'reference_name':f.fee , 'docstatus':1} , ['distinct parent'])
			for jv in jvs:
				journal_entry = frappe.get_doc('Journal Entry',jv.parent)
				if journal_entry.voucher_type != "Disenrollment Entry":
					journal_entry.cancel()

			# delete fees which is not wanted to disenroll
			if not f.disenroll:
				frappe.db.delete('Program Disenrollment Fees' , {'name' : f.name})
				continue
			if f.type == "Enrollment Fee":
				has_enrollment_fee = True
			fee = frappe.get_doc("Fees" , f.fee)
			journal_amount += self.get_journal_amount(fee.name)
			self.cancel_fee(fee)
		if journal_amount:
			self.create_journal_entry(journal_amount)
			self.db_set('unpaid_balance',journal_amount)
		if self.type == "انتقال":
			self.create_move_journal_entry()
		if has_enrollment_fee:
			self.mark_student_as_unactive()
		self.calc_unpaid_balance()

	def mark_student_as_unactive(self):
		sg = frappe.get_doc("Student Group", self.student_group)
		sgs_note = "منقول" if self.type == "انتقال" else "منسحب"
		sg.change_student_active_field(self.student, self, False, sgs_note)

	def mark_student_as_active(self):
		sg = frappe.get_doc("Student Group", self.student_group)
		sg.change_student_active_field(self.student, self)

	def create_journal_entry(self,journal_amount):
		journal_entry = frappe.get_doc({
			"doctype" : "Journal Entry",
			"voucher_type" : "Journal Entry",
			"posting_date" : self.date,
			"apl": "Low",
			"company" : frappe.db.get_value("Program Enrollment" , self.program_enrollment , 'company')
		})
		journal_entry.append('accounts' , {
			'account' : frappe.db.get_value('Company' , journal_entry.company , 'student_account'),
			'party_type' : 'Student',
			'party' : self.student,
			'debit_in_account_currency' : journal_amount
		})
		journal_entry.append('accounts' , {
			'account' : frappe.db.get_value('Company' , journal_entry.company , 'freezed_student_account'),
			'party_type' : 'Student',
			'party' : self.student,
			'credit_in_account_currency' : journal_amount
		})
		journal_entry.insert()
		journal_entry.submit()
		self.db_set("journal_entry",journal_entry.name)
	
	def create_move_journal_entry(self):
		journal_entry = frappe.get_doc({
			"doctype" : "Journal Entry",
			"voucher_type" : "Disenrollment Entry",
			"program_disenrollment": self.name,
			"posting_date" : self.date,
			"apl": "Low",
			"company" : frappe.db.get_value("Program Enrollment" , self.program_enrollment , 'company')
		})
		total = 0 
		for new_fee in self.new_fees:
			cost_center = frappe.db.get_value("Fees", new_fee.fee, "cost_center")
			journal_entry.append("accounts",{
				'account' : frappe.db.get_value('Company' , journal_entry.company , 'student_account'),
				'party_type': "Student",
				'party': self.student,
				'credit_in_account_currency': new_fee.transfered_amount,
				'reference_type': 'Fees',
				'reference_name': new_fee.fee,
				'cost_center': cost_center
			})
			total += new_fee.transfered_amount
		journal_entry.append("accounts",{
			'account' : frappe.db.get_value('Company' , journal_entry.company , 'freezed_student_account'),
			'party_type' : 'Student',
			'party' : self.student,
			'debit_in_account_currency' : total,
			'cost_center': frappe.db.get_value('Company' , journal_entry.company , 'cost_center')
		})
		journal_entry.insert()
		journal_entry.submit()
	# called from submit and cancel of journal entry of type disenrollment entry
	def calc_unpaid_balance(self):
		unpaid_balance = self.total_freezed_balance
		journal_entries = frappe.get_list("Journal Entry", filters = {"voucher_type": "Disenrollment Entry", "docstatus": 1, "program_disenrollment": self.name}, fields = ["name"])
		for je in journal_entries:
			journal_entry = frappe.get_doc("Journal Entry", je.name)
			company = frappe.get_doc("Company", journal_entry.company)
			for jea in journal_entry.accounts:
				if jea.party_type == "Student" and jea.party == self.student and jea.account == company.freezed_student_account:
					unpaid_balance -= jea.debit_in_account_currency
					unpaid_balance += jea.credit_in_account_currency
		self.db_set('unpaid_balance',unpaid_balance)
		if self.docstatus == 1:
			if unpaid_balance == 0:
				self.db_set('workflow_state', 'Paid')
			else:
				self.db_set('workflow_state', 'UnPaid')

	# get amounts from journal entry and payment entry
	@frappe.whitelist()
	def get_journal_amount(self, fee):
		journal_amount = 0 
		#get amount from payment entries
		payment_entries_names = frappe.get_list('Payment Entry Reference' , filters = {'reference_name' : fee} , fields = ['name' , 'parent','allocated_amount'])
		for pen in payment_entries_names:
			pe = frappe.get_doc('Payment Entry' , pen.parent)
			if pe.docstatus == 1:
				journal_amount += pen.allocated_amount
		#get amount from journal entry (type Disenrollment Entry) in case of student disenrollment 
		journal_entries_names = frappe.get_list('Journal Entry Account', filters = {'reference_type': 'Fees', 'reference_name': fee}, fields = ['name', 'parent', 'credit_in_account_currency'])
		for jen in journal_entries_names:
			je = frappe.get_doc('Journal Entry', jen.parent)
			if je.docstatus == 1 and je.voucher_type == "Disenrollment Entry":
				journal_amount += jen.credit_in_account_currency
		if not journal_amount: 
			frappe.response['message'] = journal_amount
		return journal_amount
	
	@frappe.whitelist()
	def get_payment_journal_doc(self):
		sg = frappe.get_doc("Student Group",self.student_group)
		freezed_account = frappe.db.get_value("Company", sg.company, "freezed_student_account")
		cash = frappe.db.get_value("Company", sg.company, "default_cash_account")
		res = frappe.new_doc("Journal Entry")
		res.voucher_type = "Disenrollment Entry"
		res.program_disenrollment = self.name
		res.apl = "Low"
		res.append("accounts",{
			"account": freezed_account,
			"debit_in_account_currency": self.unpaid_balance,
			"party_type": "Student",
			"party": self.student
		})
		res.append("accounts",{
			"account": cash,
			"credit_in_account_currency": self.unpaid_balance
		})
		return res

	


	def cancel_fee(self, fee):
		dvs = frappe.get_list('Discount Voucher' , filters = {'apply_for_fee' : fee.name , 'docstatus' : 1} , fields=['name'])
		for dv in dvs :
			discount_voucher = frappe.get_doc('Discount Voucher' , dv)
			discount_voucher.cancel()
		fee.reload()
		payments = frappe.get_list("Payment Entry Reference", filters = {"reference_doctype": "Fees", "reference_name": fee.name}, fields = ["distinct parent"])
		journals_references = frappe.get_list("Journal Entry Account", filters = {"reference_type": "Fees", "reference_name": fee.name}, fields = ["name", "parent"])
		journals = frappe.get_list("Journal Entry Account", filters = {"reference_type": "Fees", "reference_name": fee.name}, fields = ["distinct parent"])
		fee.cancel()
		company = frappe.db.get_value("Program Enrollment" , self.program_enrollment , 'company')
		cost_center = frappe.db.get_value("Company", company, "cost_center") if self.type == "انتقال" else fee.cost_center
		for p in payments:
			frappe.db.set_value("Payment Entry", p.parent, "cost_center", cost_center)
			frappe.db.sql("update `tabGL Entry` set cost_center = %s where voucher_type = 'Payment Entry' and voucher_no = %s",
			(cost_center, p.parent))
		for ref in journals_references:
			frappe.db.set_value("Journal Entry Account", ref.name, "cost_center", cost_center)
		for journal in journals:
			frappe.db.sql("update `tabGL Entry` set cost_center = %s where voucher_type = 'Journal Entry' and voucher_no = %s",
			(cost_center, journal.parent))




