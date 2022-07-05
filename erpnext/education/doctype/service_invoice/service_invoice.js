// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Service Invoice', {
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
	onload: function (frm) {
		frm.set_query('mode_of_payment',function(){
			let lis = null ;
			frappe.call(
		   {
				method : 'get_user_mode_of_payment',
			   args :{
				'user' : (frappe.session.user)
			   },
		   callback : function(res) {
			lis = res.message;
			},
			async : false
			});
			return {
				'filters' : [['Mode of Payment','name','in', lis.join(',')]]
			};
		});
	}
});

frappe.ui.form.on('Service Invoice Item', {
	
	item_code: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		frappe.call({
			method: 'get_item_account',
			doc: frm.doc,
			args: {
				'item': row.item_code
			},
			callback: function (r) {
				row.account = r.message.income_account;
				row.cost_center = r.message.selling_cost_center;
			}
		});
	},
	rate: calc_amount,
	qty: calc_amount,
	discount_amount: calc_amount,
	amount: calc_totals
});

function calc_amount(frm, cdt, cdn) {
	var row = locals[cdt][cdn]
	row.amount = row.rate * row.qty - row.discount_amount;
	frm.refresh_fields('services');
	calc_totals(frm, cdt, cdn);
}
function calc_totals(frm, cdt, cdn) {
	var total = 0;
	frm.doc.services.forEach(function (service) {
		total += service.amount;
	});
	frm.set_value('grand_total', total);
	frm.set_value('outstanding_amount',total);
}