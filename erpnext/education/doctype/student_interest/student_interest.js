// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Student Interest', {

	refresh: function(frm) {
		if(frm.doc.status != 'تم التسجيل'){
			frm.add_custom_button('New Comminucation', function(){
				frappe.prompt(
					[
						{
							'label': 'Status',
							'fieldname': 'new_status',
							'fieldtype': 'Select',
							'options': ["خارج التغطية","لم يرد","رغبة","مهتم","مهتم لكن السعر","مهتم لكن التوقيت","سيرد خبر","سيسجل اكيد","غير مهتم","غير ذلك"]
						},
						{
							'label': 'Channel',
							'fieldname': 'channel',
							'fieldtype': 'Select',
							'options': ['Message', 'Visit', 'Phone Call']
						},
						{
							'label': 'Message',
							'fieldname': 'message',
							'fieldtype': 'Small Text'
						},
						{
							'label': 'Respond',
							'fieldname': 'respond',
							'fieldtype': 'Small Text'
						},
						{
							'label': 'Note',
							'fieldname': 'note',
							'fieldtype': 'Small Text'
						}

					], (values)=>{
						frappe.call({
							method: 'add_communication_log',
							doc: frm.doc,
							args: {
								'values': values,
							},
							callback: function(r){
								frappe.msgprint('Log Created');
								frm.reload_doc();
							}

						})
					});
			});
		}

	},
	onload_post_render : function (frm) {
	    frm.fields_dict.prospective_phone.$input.on('focusout' , function(){
            if (frm.doc.prospective_phone.length != 10 || !/\d/.test(frm.doc.prospective_phone)){
                frappe.msgprint(__("Enter a valid Mobile Number"));
                frm.set_value('prospective_phone','');
			}
			else {
				frm.trigger("program");
			}
	    }
	    );
	},
	program: function (frm) {
		frappe.call({
			method: 'validate_duplicate',
			doc: frm.doc
		});
	}
});
