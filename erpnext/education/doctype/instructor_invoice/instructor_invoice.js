// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Instructor Invoice', {
	refresh: function(frm) {
		if (frm.doc.docstatus > 0) {
			frm.add_custom_button(__('Accounting Ledger'), function () {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.posting_date,
					to_date: moment(frm.doc.modified).format('YYYY-MM-DD'),
					company: frm.doc.company,
					group_by: '',
					show_cancelled_entries: frm.doc.docstatus === 2
				};
				frappe.set_route("query-report", "General Ledger");
			}, __("View"));
			
			frm.add_custom_button(__("Payments"), function() {
				frappe.set_route("List", "Payment Entry", {"Payment Entry Reference.reference_name": frm.doc.name});
			}, __("View"));

		}
		if(frm.doc.docstatus===1 && frm.doc.outstanding_amount!=0) {
			frm.add_custom_button(__("Payment"), function() {
				frm.events.make_payment_entry(frm);
			}, __('Create'));
			frm.page.set_inner_btn_group_as_primary(__('Create'));
		}
	},
	amount_per_hour:function(frm){
		frm.set_value('grand_total', frm.doc.total_count_hour * frm.doc.amount_per_hour);
	},
	total_count_hour:function(frm){
		frm.trigger("amount_per_hour");
	},
	amount_dependent_on_percent : function(frm){
		frm.set_value('grand_total', frm.doc.amount_dependent_on_percent);
	},
	grand_total : function(frm){
        frm.set_value('outstanding_amount' , frm.doc.grand_total);
	},
	student_group:function(frm){
		if( ! (frm.doc.student_group) || ! (frm.doc.instructor)){
		   frm.set_value('instructor_attendance',[]);
		   frm.set_value('grand_total',0);
		   frm.set_value('amount_per_hour',0);
		   frm.set_value('outstanding_amount',0);
		   frm.set_value('cost_center',0);
		   frm.set_value('total_count_hour',0);
		   frm.set_value('grand_total',0);
		   frm.refresh_fields;
		}
	},
	instructor:function(frm){
		frm.trigger('student_group');
	},
	onload:function(frm){
		frm.set_query('student_group',function(){
			return{
			   'filters':[
				   ['Student Group','is_paid',"=",false]
			   ]
		   };
		});
	},
	make_payment_entry: function(frm) {
		return frappe.call({
			method: "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry",
			args: {
				"dt": frm.doc.doctype,
				"dn": frm.doc.name
			},
			callback: function(r) {
				var doc = frappe.model.sync(r.message);
				frappe.set_route("Form", doc[0].doctype, doc[0].name);
			}
		});
	}
});

frappe.ui.form.on('Instructor Invoice Attendance', {
	instructor_attendance_remove : function(frm){
	var sum = 0 ;
	frm.doc.instructor_attendance.forEach(function(item){
		sum += parseFloat(item.count_of_hours);
	});
	frm.set_value('total_count_hour' , sum);
	
}
});
