// Copyright (c) 2015, Frappe Technologies and contributors
// For license information, please see license.txt

cur_frm.add_fetch('fee_structure', 'total_amount', 'amount');

frappe.ui.form.on("Program", "refresh", function(frm) {
    if(!frm.doc.__local && frappe.user.has_role("Sales Manager - Edu")){
        frm.add_custom_button("Change Values", function(){
            frappe.prompt([
                {
                    label: "Interest Expiry Duration",
                    fieldname: "interest_expiry_duration",
                    fieldtype: "Data"
                },
                {
                    label: "Salesman Owner",
                    fieldname: "salesman_owner",
                    fieldtype: "Link",
                    options: "Salesman"
                }
            ], (values)=>{
                frappe.call({
                    method: "erpnext.education.api.set_program_values",
                    args:{
                        args:{
                            name: frm.doc.name,
                            ...values
                        }
                    }
                }).then(_=>{
                    frm.reload_doc();
                })
            });
        });
    }
});