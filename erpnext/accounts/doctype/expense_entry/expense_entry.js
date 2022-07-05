// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Expense Entry', {

	refresh: function(frm) {

		if(frm.doc.docstatus > 0) {
			frm.add_custom_button(__('Accounting Ledger'), function() {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.posting_date,
					to_date: moment(frm.doc.modified).format('YYYY-MM-DD'),
					company: frm.doc.company,
					group_by: '',
					show_cancelled_entries: frm.doc.docstatus === 2
				};
				frappe.set_route("query-report", "General Ledger");
			}, __("View"));}



	},

    calc_total_credit:function(frm){
        var t;
        t=frm.doc.conversion_rate*frm.doc.paid_amount;
        frm.set_value('total_credit',t);
    },
    
    
    
    
    calc_total_debit:function(frm){
        var t=0;
        frm.doc.account.forEach(k=>{
            t+=k.amount;
        });
        t*=frm.doc.conversion_rate;
        frm.set_value('total_debit',t);
    },

    posting_date : function(frm){
        frappe.call({
            method : 'erpnext.setup.utils.get_exchange_rate',
            args : {
                'from_currency' : frm.doc.account_currency,
                'to_currency' : frappe.defaults.get_user_default("currency"),
                'transaction_date' : frm.doc.posting_date
            },
            callback : function(r){
                frm.set_value('conversion_rate' , r.message);
            }
            
        });  
    },

    company: function(frm) {
       frm.set_value('mode_of_payment',"");
    },



    mode_of_payment : function(frm) {
        if(frm.doc.mode_of_payment){    
        	frappe.db.get_doc('Mode of Payment',frm.doc.mode_of_payment)
        	.then(doc=>{
        	    doc.accounts.forEach(i=>{
                    if(i.company==frm.doc.company){
                    frm.set_value('account_paid_from',i.default_account);
                    return;
                    }
                });
            });
        }
        else{
            frm.set_value('account_paid_from',"");
        }
},



 
    onload:function(frm){
        frm.trigger("posting_date");  
        frm.set_query('account','account',function(doc,cdt,cdn){
           return{
               'filters':[
                   ['Account','company',"=",frm.doc.company],
                   ['Account','account_currency',"=",frm.doc.account_currency],
                   ['Account','account_type','=',"Expense Account"],
                   ['Account','is_group','=',false]
               ]
           };
        });
        frm.set_query('cost_center','account',function(doc,cdt,cdn){
           return{
               'filters':[
                   ['Cost Center','company',"=",frm.doc.company],
                   ['Cost Center','is_group','=',false]
               ]
           };
        });
    },



    paid_amount:function(frm){
        frm.trigger("calc_total_credit");
    },
    
    
    
    conversion_rate:function(frm){
        frm.trigger("calc_total_credit");
        frm.trigger("calc_total_debit");
    }
});
   
frappe.ui.form.on('Expense Entry Account', {
	account_add: function(frm,cdt,cdn) {
        var row = locals[cdt][cdn];
    	frappe.db.get_doc('Company',frm.doc.company)
    	.then(doc=>{
    	    row.cost_center = doc.cost_center;
    	    frm.refresh_fields(); 
        });
    },
    
    
    
    amount:function(frm,cdt,cdn){
        frm.trigger("calc_total_debit");
    },
    
    
    
    account_remove:function(frm,cdt,cdn){
        frm.trigger("calc_total_debit");
    }
});