import frappe
from frappe import _
from erpnext.education.doctype.fees.fees import Fees
from frappe.utils import now


class CustomFees(Fees):
	def before_cancel(self):
		super(CustomFees,self).before_cancel()
		self.remove_cost_center()

	def remove_cost_center(self):
		cost_center = frappe.db.get_value("Company", self.company, "cost_center")
		self.remove_cost_center_from_jv()
		self.remove_cost_center_from_pe()
		frappe.db.sql("""update `tabGL Entry`
            set cost_center=%s,
            modified=%s, modified_by=%s
            where against_voucher_type=%s and against_voucher=%s
            and voucher_no != ifnull(against_voucher, '')""",
            (cost_center ,now(), frappe.session.user, self.doctype, self.name))

	def remove_cost_center_from_jv(self):
		cost_center = frappe.db.get_value("Company", self.company, "cost_center")
		linked_jv = frappe.db.sql_list("""select parent from `tabJournal Entry Account`
			where reference_type=%s and reference_name=%s and docstatus < 2""", ("Fees", self.name))
		if linked_jv:
			frappe.db.sql("""update `tabJournal Entry Account`
				set cost_center=%s,
				modified=%s, modified_by=%s
				where reference_type=%s and reference_name=%s
				and docstatus < 2""", (cost_center,now(), frappe.session.user, "Fees", self.name))

	def remove_cost_center_from_pe(self):
		cost_center = frappe.db.get_value("Company", self.company, "cost_center")
		linked_pes = frappe.get_list("Payment Entry Reference", filters={"reference_doctype": "Fees", "reference_name": self.name}, fields=["parent"])

		for lp in linked_pes:
			frappe.db.set_value("Payment Entry", lp.parent, "cost_center", cost_center)





