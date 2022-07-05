// Copyright (c) 2016, Frappe and contributors
// For license information, please see license.txt


frappe.ui.form.on('Program Enrollment', {
	setup: function(frm) {
		frm.add_fetch('fee_structure', 'total_amount', 'amount');
	},

	onload: function(frm) {
		frm.set_query('academic_term', function() {
			return {
				'filters':{
					'academic_year': frm.doc.academic_year
				}
			};
		});

		frm.set_query('academic_term', 'fees', function() {
			return {
				'filters':{
					'academic_year': frm.doc.academic_year
				}
			};
		});

		frm.set_query('student_group', function () {
			return {
				'filters': [
					['Student Group', 'academic_year', '=', frm.doc.academic_year],
					['Student Group', 'program', '=', frm.doc.program],
					['Student Group', 'status', '=', 'Available'],
					['Student Group', 'type', '=', frm.doc.student_group_type],
					['Student Group', 'company', '=', frm.doc.company]
				]
			}
		})

		if (frm.doc.program) {
			frm.set_query('course', 'courses', function() {
				return {
					query: 'erpnext.education.doctype.program_enrollment.program_enrollment.get_program_courses',
					filters: {
						'program': frm.doc.program
					}
				}
			});
		}
	},

	program: function(frm) {
		frm.events.get_courses(frm);
		if (frm.doc.program) {
			frappe.call({
				method: 'erpnext.education.api.get_fee_schedule',
				args: {
					'program': frm.doc.program,
					'student_category': frm.doc.student_category
				},
				callback: function (r) {
					if (r.message) {
						frm.set_value('fees' ,r.message);
						frm.events.get_courses(frm);
					}
				}
			});
		}
	},

	student_category: function() {
		frappe.ui.form.trigger('Program Enrollment', 'program');
	},

	get_courses: function (frm) {
		frm.set_value('courses',[]);
		frappe.call({
			method: 'get_courses',
			doc:frm.doc,
			callback: function(r) {
				if (r.message) {
					frm.set_value('courses', r.message);
				}
			}
		})
	}
});


frappe.ui.form.on('Program Fee',{
	fees_add: function (frm) {
		frm.fields_dict['fees'].grid.get_field('fee_structure').get_query = function (doc, cdt, cdn) {
			var d = locals[cdt][cdn];
			var fs_list = [];
			if (!doc.__islocal) fs_list.push(doc.name);
			$.each(doc.fees, function (_idx, val) {
				if (val.fee_structure) fs_list.push(val.fee_structure);
			});
			return {
				filters: [
					["Fee Structure", 'program', '=', frm.doc.program],
					["Fee Structure", 'docstatus', '=', 1],
					["Fee Structure", 'status', '=', 'Active'],
					["Fee Structure", 'company', '=', frm.doc.company],
					['Fee Structure', 'name', 'not in', fs_list]
					
				]
			}
		};
	}
});


frappe.ui.form.on('Program Enrollment Course', {
	courses_add: function(frm){
		frm.fields_dict['courses'].grid.get_field('course').get_query = function(doc) {
			var course_list = [];
			if(!doc.__islocal) course_list.push(doc.name);
			$.each(doc.courses, function(_idx, val) {
				if (val.course) course_list.push(val.course);
			});
			return { filters: [['Course', 'name', 'not in', course_list]] };
		};
	}
});