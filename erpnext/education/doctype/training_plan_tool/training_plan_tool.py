# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import math
from frappe.model.document import Document
from frappe.utils import flt

class TrainingPlanTool(Document):
	@frappe.whitelist()
	def get_top_programs(self):
		self.programs = []
		#program count
		p_count = math.ceil(flt(self.count_of_group) * flt(self.top_course) /(100 * flt(self.repetition_t)))
		#top programs
		programs = frappe.db.sql("select program , count(*) as c from `tabProgram Enrollment` where student_group_type = 'General Course' and company = %(company)s group by program order by c desc limit "+ str(p_count),values = {'company': self.company}, as_dict = True)

		self.append_to_programs(programs, self.repetition_t)
		high_income_programs = self.get_low_high_income_programs()
		self.append_to_programs(high_income_programs, self.repetition_h)
		low_income_programs = self.get_low_high_income_programs(is_low= True)
		self.append_to_programs(low_income_programs, self.repetition_l)
		self.calc_totals()


	def append_to_programs(self, tab, repetition):
		#Avg Room Capacity
		default_stu_count = get_default_stu_count(self.company)
		for t in tab:
			#Student Group Avg Students
			stu_count = get_avg_stu_count(t['program'])
			if not stu_count:
				stu_count = default_stu_count
			
			fee_amount = frappe.db.get_value('Fee Structure', {'program': t['program'], 'status': 'Active', 'company': self.company, 'description': "Enrollment Fee"} , 'total_amount') or 0
			self.append('programs',{
				'program': t['program'],
				'repetition': repetition,
				'stu_count': stu_count,
				'enrollment_fee': fee_amount,
				'estimated_income': flt(fee_amount) * flt(stu_count) * flt(repetition)
			})
	
	def is_exist_program(self, program):
		for p in self.programs:
			if p.program == program:
				return True
		return False

	def get_low_high_income_programs(self, is_low = False):
		operation = "asc" if is_low else "desc"
		high_or_low = self.low_income if is_low else self.high_income
		repetition = self.repetition_l if is_low else self.repetition_h
		query = """select p.name , fs.total_amount/p.hours as c from tabProgram as p join `tabFee Structure` as fs on fs.program = p.name where fs.status = 'Active' and fs.description = 'Enrollment Fee' and fs.company = %(company)s order by c """ + operation
		l = frappe.db.sql(query, values = {'company': self.company} ,as_dict = True)
		res = []
		res_len = math.ceil(flt(self.count_of_group) * flt(high_or_low) /(100 * flt(repetition)))
		index = 0
		while(len(res) < res_len):
			if index >= len(l):
				break
			if not self.is_exist_program(l[index].name):
				res.append({'program': l[index].name})
			index += 1
		return res
	@frappe.whitelist()
	def calc_totals(self):
		exp_total = 0
		for p in self.programs:
			exp_total += flt(p.estimated_income)
		self.plan_income_expected = exp_total
		self.difference = self.plan_income_expected - self.required_income
	@frappe.whitelist()
	def get_courses_count_in_period(self):
		from_date = frappe.utils.add_to_date(self.from_date, years = -1)
		till_date = frappe.utils.add_to_date(self.till_date, years = -1)
		count = frappe.db.sql("select count(name) as c from `tabStudent Group` where company = %(company)s and (start_date between %(from_date)s and %(till_date)s ) ", values = {
			'company': self.company,
			'from_date': from_date,
			'till_date': till_date
		}, as_dict = True)
		self.courses_count_in_period = count[0].c




def get_avg_stu_count(program):
	avg = frappe.db.sql("select avg(student_count) as avg from `tabStudent Group` where program = %(program)s and type = 'General Course'", values = {'program': program}, as_dict = True)
	return avg[0].avg

def get_default_stu_count(company):
	avg = frappe.db.sql("select avg(seating_capacity) as avg from tabRoom where company = %(company)s ", values = {'company': company},as_dict = True)
	return avg[0].avg
