# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, flt, add_to_date

class RepostDeferredRevenue(Document):
	def before_submit(self):
		query = """
		select cost_center, sum(credit) - sum(debit) as balance from `tabGL Entry`
		where is_cancelled = 0 and account = %(account)s and company = %(company)s
		group by cost_center
		"""
		company = frappe.get_doc("Company", self.company)
		journal_entry = frappe.get_doc({
			"doctype": "Journal Entry",
			"company": company.name,
			"posting_date": self.repost_date
		})
		deferred_balances = dict(frappe.db.sql(query,values={
			"account": company.default_deferred_income_account_for_fee,
			"company": company.name
		}))
		income_balances = dict(frappe.db.sql(query,values={
			"account": company.default_income_account,
			"company": company.name
		}))
		for cost_center, balance in deferred_balances.items():
			sg = frappe.db.get_value("Student Group", {"cost_center": cost_center}, ["name", "total_hours", "actual_hours", "status"], as_dict=1)
			if not sg:
				continue
			achievement_percent = flt(flt(sg.actual_hours) / flt(sg.total_hours) *100, 1)
			if achievement_percent > 100 or sg.status == "Finished":
				achievement_percent = 100
			income_balance = income_balances.get(cost_center, 0)
			total_balance = balance + income_balance
			current_achievement_percent = flt(income_balance / total_balance *100 ,1)
			amount = (achievement_percent - current_achievement_percent) /100 * total_balance
			if amount:
				deferred_debit_or_credit = "debit" if amount > 0 else "credit" 
				income_debit_or_credit = "debit" if deferred_debit_or_credit == "credit" else "credit"
				journal_entry.append("accounts", {
					"account": company.default_deferred_income_account_for_fee,
					"cost_center": cost_center,
					deferred_debit_or_credit + "_in_account_currency": abs(amount)
				})
				journal_entry.append("accounts", {
					"account": company.default_income_account,
					"cost_center": cost_center,
					income_debit_or_credit + "_in_account_currency": abs(amount)
				})
				self.append("details", {
					"cost_center": cost_center,
					"deferred_account": company.default_deferred_income_account_for_fee,
					"income_account": company.default_income_account,
					"actual_achievement_percent": achievement_percent,
					"achievement_percent": current_achievement_percent,
					"amount": amount
				})
		if journal_entry.get("accounts"):
			journal_entry.insert()
			journal_entry.submit()
			self.journal_entry = journal_entry.name
	
	def on_cancel(self):
		if self.get("journal_entry"):
			je = frappe.get_doc("Journal Entry", self.journal_entry)
			frappe.db.set_value(self.doctype, self.name, "journal_entry", None)
			je.cancel()
			je.delete()


def repost_all_cost_centers():
	companies = frappe.get_list("Company", filters={"enable_repost_deferred_revenue": 1}, pluck="name")
	for company in companies:
		repost_deferred_revenue = frappe.get_doc({
			"doctype": "Repost Deferred Revenue",
			"company": company,
			"repost_date": add_to_date(nowdate(), days=-1, as_string=True)
		})
		repost_deferred_revenue.insert()
		repost_deferred_revenue.submit()
		