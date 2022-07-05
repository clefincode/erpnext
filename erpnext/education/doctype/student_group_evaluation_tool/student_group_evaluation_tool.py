# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe.model.document import Document

class StudentGroupEvaluationTool(Document):
	@frappe.whitelist()
	def get_students_count(self):
		return frappe.db.count('Student Group Student', {'active': True, 'parent': self.student_group})

	@frappe.whitelist()
	def get_student_group_data(self):
		columns = self.get_columns()
		data = self.get_data()
		has_data = frappe.db.count("Student Group Evaluation",{'student_group': self.student_group})
		return columns, data, True if has_data else False

	@frappe.whitelist()
	def create_student_group_evaluations(self, data):
		for d in data:
			for key,value in d.items():
				if frappe.db.exists("Evaluation Question", d['question']):
					if key != "question":
						sge = frappe.get_doc({
							"doctype": "Student Group Evaluation",
							"student_group": self.student_group,
							"student": key,
							"evaluation_question": d['question'],
							"category": self.get_question_category(d['question']),
							"evaluation": value
						})
						sge.insert()
	
	def get_question_category(self, question):
		program = frappe.db.get_value('Student Group', self.student_group, ['program'])
		template_name = frappe.db.get_value("Program", program, "evaluation_template")
		category = frappe.db.get_value("Evaluation Template Items", {'parent': template_name, 'evaluation_question': question})
		return category

		
	def get_columns(self):
		columns = [{
			'name': "Question",
			'id': "question",
			'editable': False,
			'width': 350
		}]
		students_count = frappe.db.count('Student Group Student', {'active':True, 'parent':self.student_group})
		for i in range(students_count):
			columns.append({
				'name': "Stu "+str(i+1),
				'id': "stu_"+str(i+1),
				'editable': True,
				'width': 120
			})
		return columns
	def get_data(self):
		student_count = frappe.db.count('Student Group Student', {'active':True, 'parent':self.student_group})
		data = []
		program = frappe.db.get_value("Student Group", self.student_group, "program")
		template_name = frappe.db.get_value("Program", program, "evaluation_template")
		template = frappe.get_doc("Evaluation Template", template_name)
		cur_catagory = None
		index = {'start': 0 , 'end':0}
		for i in range(len(template.evaluation_template_items)):
			q = template.evaluation_template_items[i]
			if not cur_catagory : 
				cur_catagory = q.category
			elif cur_catagory != q.category:
				index['end'] = len(data)
				row = calculate_avg(data, index, student_count, cur_catagory)
				data.append(row)
				index['start'] = len(data)
				cur_catagory = q.category
			row = {"question":q.evaluation_question}
			row = self.initilize_row(row, student_count)
			data.append(row)
		index['end'] = len(data)
		row = calculate_avg(data, index, student_count, template_name)
		data.append(row)
		return data

	def initilize_row(self, row, student_count):
		row_data = frappe.get_list("Student Group Evaluation", filters = {'student_group': self.student_group, "evaluation_question": row['question']}, fields = ["*"])
		for d in row_data:
			row.update({d.student: d.evaluation})
		for i in range(student_count):
			if row.get('stu_'+str(i+1)) == None:
				row.update({'stu_'+str(i+1): 0})
		return row

def calculate_avg(data, index, student_count, category):
	row = {}
	avg_all = 0
	for i in range(1,student_count+1):
		avg = 0
		for j in range(index['start'], index['end']):
			avg = avg + flt(data[j]['stu_' + str(i)])
		avg /= (index['end'] - index['start'])
		avg_all += avg
		row.update({'stu_'+str(i): flt(avg,2)})
	row.update({'question': '{0} ({1})'.format(category ,flt(avg_all/student_count,2))})
	res_row = {}
	for key, value in row.items():
		res_row.update({
			key: {
				'content': value,
				'editable': False,
				'avg': 1
			}
		})

	return res_row
	
		

