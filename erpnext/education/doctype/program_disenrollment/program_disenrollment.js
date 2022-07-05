// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Program Disenrollment', {
    //============================================================
    onload:function(frm){
        frm.set_query('program_enrollment',function(){
            return{
               'filters':[
                   ['Program Enrollment','student',"=",frm.doc.student],
                   ['Program Enrollment','docstatus',"=",1],
               ]
           };
            });
},
//================================================================
	student:function(frm){
		frm.set_value('program_enrollment',"");
	},
	refresh: function(frm){
        if (/*frm.doc.unpaid_balance &&*/ frm.doc.docstatus == 1)
            frm.add_custom_button('Pay', () => {
                frappe.call({
                    method: "get_payment_journal_doc",
                    doc: frm.doc,
                    args: {},
                    callback: function (res) {
                        var doc = frappe.model.sync(res.message);
                        frappe.set_route("Form", doc[0].doctype, doc[0].name);
                    }
                    });
            });
	},
//==============================================================
    program_enrollment:function(frm){
        if(!frm.doc.program_enrollment){
            frm.set_value('fees',[]);
        }
        else{
            frappe.db.get_list('Fees',{
                fields:['name','grand_total','outstanding_amount','fees_category', 'total_discount_applied_for_this_fee'],
                filters:{
                    'docstatus':1,
                    'program_enrollment':frm.doc.program_enrollment
                }
            }).then(f=>{
                frm.doc.fees = [];
                f.forEach(i=>{
                frm.add_child('fees',{'fee':i.name,
                                      'type':i.fees_category,
                                      'grand_total':i.grand_total,
                                      'paid_amount':(i.grand_total) - (i.outstanding_amount) - (i.total_discount_applied_for_this_fee),
                                      'outstanding_amount':i.outstanding_amount
                });
                });
                frm.refresh_fields();
            });
        }
	},
	new_program_enrollment:function(frm){
        if(!frm.doc.new_program_enrollment){
            frm.set_value('new_fees',[]);
        }
        else{
            frappe.db.get_list('Fees',{
                fields:['name','outstanding_amount','fees_category', 'grand_total'],
                filters:{
                    'docstatus':1,
                    'program_enrollment':frm.doc.new_program_enrollment
                }
            }).then(f=>{
                frm.doc.new_fees = [];
                f.forEach(i=>{
                frm.add_child('new_fees',{'fee':i.name,
                                      'type':i.fees_category,
                                     'grand_total': i.grand_total,
                                      'outstanding_amount':i.outstanding_amount
                                      
                });
                });
                frm.refresh_fields();
            });
        }
    },
  //============================================================  
});
frappe.ui.form.on("Program Disenrollment Fees", {
    fees_add: function (frm, cdt, cdn) {
        calc_total_freezed_balance(frm)
    },
    fees_remove: function (frm, cdt, cdn) {
        calc_total_freezed_balance(frm)
    },
    disenroll: function (frm, cdt, cdn) {
        calc_total_freezed_balance(frm)
    }
})

function calc_total_freezed_balance(frm) {
    var total = 0;
    for (var i = 0; i < frm.doc.fees.length; i++) {
        
        if (frm.doc.fees[i].disenroll == 1) {
            frappe.call({
                method: "get_journal_amount",
                doc: frm.doc,
                args: {
                    'fee': frm.doc.fees[i].fee
                },
                callback: function (res) {
                    total += parseFloat(res.message);
                },
                freeze: true,
                async: false
            });
        }
    }
    frm.set_value("total_freezed_balance", total);
    frm.set_value("unpaid_balance", total);
}
