# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe.model.document import Document
from frappe import _
from erpnext.education.utils import validate_duplicate_student
from frappe.utils import cint

class StudentGroup(Document):
	def validate(self):
		self.validate_mandatory_fields()
		self.validate_strength()
		self.validate_students()
		self.validate_and_set_child_table_fields()
		self.calculate_active_student_count()
		validate_duplicate_student(self.students)
	
	def validate_mandatory_fields(self):
		if self.group_based_on == "Course" and not self.course:
			frappe.throw(_("Please select Course"))
		if self.group_based_on == "Course" and (not self.program and self.batch):
			frappe.throw(_("Please select Program"))
		if self.group_based_on == "Batch" and not self.program:
			frappe.throw(_("Please select Program"))

	def validate_strength(self):
		if cint(self.max_strength) < 0:
			frappe.throw(_("""Max strength cannot be less than zero."""))
		active_student = 0 
		for stu in self.students:
			if stu.active:
				active_student +=1
		if self.max_strength and active_student > self.max_strength:
			frappe.throw(_("""Cannot enroll more than {0} students for this student group.""").format(self.max_strength))

	def validate_students(self):
		program_enrollment = get_program_enrollment(self.academic_year, self.academic_term, self.program, self.batch, self.student_category, self.course)
		students = [d.student for d in program_enrollment] if program_enrollment else []
		for d in self.students:
			if not frappe.db.get_value("Student", d.student, "enabled") and d.active and not self.disabled:
				frappe.throw(_("{0} - {1} is inactive student").format(d.group_roll_number, d.student_name))

			if (self.group_based_on == "Batch") and cint(frappe.defaults.get_defaults().validate_batch)\
				and d.student not in students:
				frappe.throw(_("{0} - {1} is not enrolled in the Batch {2}").format(d.group_roll_number, d.student_name, self.batch))

			if (self.group_based_on == "Course") and cint(frappe.defaults.get_defaults().validate_course)\
				and (d.student not in students):
				frappe.throw(_("{0} - {1} is not enrolled in the Course {2}").format(d.group_roll_number, d.student_name, self.course))

	def validate_and_set_child_table_fields(self):
		roll_numbers = [d.group_roll_number for d in self.students if d.group_roll_number]
		max_roll_no = max(roll_numbers) if roll_numbers else 0
		roll_no_list = []
		for d in self.students:
			if not d.student_name:
				d.student_name = frappe.db.get_value("Student", d.student, "title")
			if not d.group_roll_number:
				max_roll_no += 1
				d.group_roll_number = max_roll_no
			if d.group_roll_number in roll_no_list:
				frappe.throw(_("Duplicate roll number for student {0}").format(d.student_name))
			else:
				roll_no_list.append(d.group_roll_number)
				
	def on_trash(self):
		cur_series = str(self.name)[str(self.name).rfind("-") + 1:]
		last_series = frappe.db.sql("select current from tabSeries where name = %s", str(self.name)[:str(self.name).rfind("-") + 1], as_dict=1)
		if (flt(cur_series) == flt(last_series[0].current)):
			wos = frappe.get_all("Student Group", fields=['name'], filters={'name': ['like', str(self.name)[:str(self.name).rfind("-") + 1] + "%"]})
			max = 0
			for wo in wos:
				if wo.name != self.name:
					seq = flt(str(wo.name)[str(wo.name).rfind("-") + 1:])
					if seq > max:
						max = seq
			frappe.db.sql("update tabSeries set current = %s  where name = %s", (max, str(self.name)[:str(self.name).rfind("-") + 1]), as_dict=1)
			frappe.msgprint("Series Updated")
	
	def create_certificate_for_student(self , student , att , assessment , is_paid_fee):
		#this function will get the cirtificate structure which is best for the parameters above
		ass_total = 0 
		if assessment != None:
			ass = frappe.get_doc('Assessment Result' , assessment)
			ass_total = ass.total_score
		certs = frappe.db.get_all('Program Certificate' , filters = {'parent' : self.program}, fields = ['certificate'] , order_by = 'priority')
		for cert in certs : 
			cs = frappe.get_doc('Certificate Structure' , cert.certificate)
			if att >= flt(cs.attendance) and flt(ass_total) >= flt(cs.assessment) and not (cs.fees_is_paid and not is_paid_fee):
				certificate = frappe.get_doc({
					'doctype' : 'Certificate',
					'student' : student,
					'student_group' : self.name,
					'certificate_structure' : cs.name,
					'assessment_result' : assessment
				})
				certificate.insert()
				try :
					certificate.submit()
				except:
					certificate.delete()
					continue
				break

	def change_student_active_field(self, student, program_enrollment, is_active = True, sgs_note = None):
		exist_student = False
		for s in self.students:
			if s.student == student:
				s.active = is_active
				if sgs_note:
					s.program_enrollment_note = sgs_note
				self.save(ignore_permissions=True)
				exist_student = True
				break
		if not exist_student and is_active:
			self.append("students" , {'student': program_enrollment.student ,'program_enrollment': program_enrollment.name,'program_enrollment_note': program_enrollment.note, 'active': is_active})
			self.save(ignore_permissions=True)


	def calculate_active_student_count(self):
		count = 0
		for s in self.students:
			if s.active:
				count += 1
		self.student_count = count


@frappe.whitelist()
def get_students(academic_year, group_based_on, academic_term=None, program=None, batch=None, student_category=None, course=None):
	enrolled_students = get_program_enrollment(academic_year, academic_term, program, batch, student_category, course)

	if enrolled_students:
		student_list = []
		for s in enrolled_students:
			if frappe.db.get_value("Student", s.student, "enabled"):
				s.update({"active": 1})
			else:
				s.update({"active": 0})
			student_list.append(s)
		return student_list
	else:
		frappe.msgprint(_("No students found"))
		return []

def get_program_enrollment(academic_year, academic_term=None, program=None, batch=None, student_category=None, course=None):

	condition1 = " "
	condition2 = " "
	if academic_term:
		condition1 += " and pe.academic_term = %(academic_term)s"
	if program:
		condition1 += " and pe.program = %(program)s"
	if batch:
		condition1 += " and pe.student_batch_name = %(batch)s"
	if student_category:
		condition1 += " and pe.student_category = %(student_category)s"
	if course:
		condition1 += " and pe.name = pec.parent and pec.course = %(course)s"
		condition2 = ", `tabProgram Enrollment Course` pec"

	return frappe.db.sql('''
		select
			pe.student, pe.student_name
		from
			`tabProgram Enrollment` pe {condition2}
		where
			pe.academic_year = %(academic_year)s  {condition1}
		order by
			pe.student_name asc
		'''.format(condition1=condition1, condition2=condition2),
                ({"academic_year": academic_year, "academic_term":academic_term, "program": program, "batch": batch, "student_category": student_category, "course": course}), as_dict=1)



@frappe.whitelist()
def get_certificates_for_student_group(sg):
	student_group = frappe.get_doc('Student Group' , sg)
	student_fees = frappe.db.sql("""SELECT GL.party ,Stu.title as "student_name",sum(GL.debit) as d ,sum(GL.credit) as c,(sum(GL.debit)-sum(GL.credit))*-1 as b 
	FROM `tabGL Entry` as GL
	LEFT JOIN tabStudent as Stu on GL.party= Stu.name
	where (GL.party_type = "Student") and (GL.is_cancelled = 0) and  (GL.cost_center = %s)
	group by GL.party ,GL.cost_center,Stu.title""",student_group.cost_center , as_dict = 1 )
     
	for stu in student_group.students:
		if stu.active:
			ass_name = frappe.db.get_value('Assessment Result' , {'docstatus' : 1 , 'student':stu.student , 'student_group' : student_group.name} , ['name']) or None
			#ass_total = frappe.db.get_value('Assessment Result' , {'docstatus' : 1 , 'student':stu.student , 'student_group' : student_group.name} , ['total_score']) or -1
			att_present_count = frappe.db.count('Student Attendance' , {'status' : 'Present' , 'student' :stu.student , 'student_group' : student_group.name , 'docstatus' : 1})
			att_absent_count = frappe.db.count('Student Attendance' , {'status' : 'Absent' , 'student' :stu.student , 'student_group' : student_group.name , 'docstatus' : 1})
			att = 0 
			try:
				att = att_present_count * 100 / (att_present_count + att_absent_count ) 
			except:
				att = 0
			is_paid_fee = False
			if student_group.type == "General Course":
				for f in student_fees : 
					if f.party == stu.student and f.b >= 0 :
						is_paid_fee = True
			else:
				is_paid_fee = True
			student_group.create_certificate_for_student(stu.student , att , ass_name , is_paid_fee)
			frappe.msgprint('ass_total {0} , att {1} , is_paid_fee {2}'.format(ass_name , att , is_paid_fee))

        #if not ar :
        #    frappe.msgprint('There Is No Assessment Result For Student {0}'.format(stu.student))
        #    continue
        



@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def fetch_students(doctype, txt, searchfield, start, page_len, filters):
	if filters.get("group_based_on") != "Activity":
		enrolled_students = get_program_enrollment(filters.get('academic_year'), filters.get('academic_term'),
			filters.get('program'), filters.get('batch'), filters.get('student_category'))
		student_group_student = frappe.db.sql_list('''select student from `tabStudent Group Student` where parent=%s''',
			(filters.get('student_group')))
		students = ([d.student for d in enrolled_students if d.student not in student_group_student]
			if enrolled_students else [""]) or [""]
		return frappe.db.sql("""select name, title from tabStudent
			where name in ({0}) and (`{1}` LIKE %s or title LIKE %s)
			order by idx desc, name
			limit %s, %s""".format(", ".join(['%s']*len(students)), searchfield),
			tuple(students + ["%%%s%%" % txt, "%%%s%%" % txt, start, page_len]))
	else:
		return frappe.db.sql("""select name, title from tabStudent
			where `{0}` LIKE %s or title LIKE %s
			order by idx desc, name
			limit %s, %s""".format(searchfield),
			tuple(["%%%s%%" % txt, "%%%s%%" % txt, start, page_len]))

