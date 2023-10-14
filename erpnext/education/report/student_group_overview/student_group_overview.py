# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"fieldname": "name",
			"fieldtype": "Link",
			"label": "Student Group",
			"options": "Student Group",
			"width": 400
		},
		{
			"fieldname": "status",
			"fieldtype": "Data",
			"label": "Status",
			"width": 100
		},
		{
			"fieldname": "start_date",
			"fieldtype": "Date",
			"label": "Start Date",
			"width": 120
		},
		{
			"fieldname": "count",
			"fieldtype": "Int",
			"label": "Count",
			"width": 70
		},
		{
			"fieldname": "date",
			"fieldtype": "Date",
			"label": "Date",
			"width": 100
		},
		{
			"fieldname": "total_fee",
			"fieldtype": "Currency",
			"label": "Total Fee",
			"width": 120
		},
		{
			"fieldname": "discounts",
			"fieldtype": "Currency",
			"label": "Discounts",
			"width": 140
		},
		{
			"fieldname": "payments",
			"fieldtype": "Currency",
			"label": "Payments",
			"width": 140
		},
		{
			"fieldname": "balance",
			"fieldtype": "Currency",
			"label": "Balance",
			"width": 140
		}
	]
def get_data(filters):
	last_result = []
	sg_filters = {
		'company': filters.company,
		'academic_year': filters.academic_year,
		'start_date': ['between' , [filters.from_date , filters.to_date]]
	}
	if filters.status:
		sg_filters.update({'status': filters.status})
	if filters.program:
		sg_filters.update({'program': filters.program})
	student_groups = frappe.get_list('Student Group' ,filters = sg_filters , fields = ['name' , 'cost_center', 'status', 'start_date'] , order_by ='start_date desc')
	for sg in student_groups:
		cur_index = len(last_result)
		total_fee = total_discounts = total_payments = balance = 0
		cur_row = {
		'indent': 0,
		'name': sg.name,
		'status': sg.status,
		'start_date': sg.start_date,
		'count': len(frappe.get_list('Student Group Student' , filters = {'parent':sg.name , 'active':1})),
		'total_fee': 0 ,
		'balance': 0,
		'allocated': 0,
		'date': frappe.get_doc('Student Group',sg.name).start_date
		}
		last_result.append(cur_row)
		res = frappe.db.sql("""select glt.party , glt.student_name , gld.discounts , glp.payments , glt.b , glt.d from (
		(SELECT GL.party ,Stu.title as "student_name", sum(GL.credit) as c ,sum(GL.debit) as d , (sum(GL.debit)-sum(GL.credit))*-1 as b
		FROM `tabGL Entry` as GL
		LEFT JOIN tabStudent as Stu on GL.party= Stu.name
		where (GL.party_type = "Student") and (GL.is_cancelled = 0) 
		and  (GL.cost_center = %(cost_center)s)
		group by GL.party ,GL.cost_center,Stu.title) glt left join
		(SELECT GL.party ,Stu.title as "student_name", sum(GL.credit) as discounts
		FROM `tabGL Entry` as GL
		LEFT JOIN tabStudent as Stu on GL.party= Stu.name
		where (GL.party_type = "Student") and (GL.is_cancelled = 0) 
		and  (GL.cost_center = %(cost_center)s)
		and (GL.voucher_type = "Discount Voucher")
		group by GL.party ,GL.cost_center,Stu.title) gld 
		on glt.party = gld.party left join 
		(SELECT GL.party ,Stu.title as "student_name", sum(GL.credit) as payments
		FROM `tabGL Entry` as GL
		LEFT JOIN tabStudent as Stu on GL.party= Stu.name
		where (GL.party_type = "Student") and (GL.is_cancelled = 0) 
		and  (GL.cost_center = %(cost_center)s)
		and (GL.voucher_type != "Discount Voucher")
		group by GL.party ,GL.cost_center,Stu.title) glp
		on glt.party = glp.party)
		""",values = sg , as_dict=1)
		for r in res:
			is_active = frappe.db.get_value('Student Group Student',{
				'student': r.party,
				'parent': sg.name
				}, 'active')
			if is_active:
				row = {
				'indent':1,
				'name': r.student_name,
				'total_fee': r.d,
				'payments': r.payments,
				'discounts': r.discounts,
				'balance': r.b,
				'count': 1,
				'date': frappe.db.get_value('Program Enrollment' , {'student': r.party , 'student_group': sg.name} , 'enrollment_date')
				}
				last_result.append(row)
				total_fee = total_fee + r.d
				total_discounts = total_discounts + (r.discounts or 0)
				total_payments = total_payments + (r.payments or 0)
				balance = balance + (r.b or 0)
		last_result[cur_index].update({'total_fee': total_fee , 'balance': balance , 'payments': total_payments , 'discounts': total_discounts})
	return last_result