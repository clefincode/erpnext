erpnext.PointOfSale.PastOrderSummary = class {
	constructor({ wrapper, events, pos_profile }) {
		this.wrapper = wrapper;
		this.events = events;
		this.pos_profile = pos_profile;

		this.init_component();
	}

	init_component() {
		this.prepare_dom();
		this.init_email_print_dialog();
		this.bind_events();
		this.attach_shortcuts();
	}

	prepare_dom() {
		this.wrapper.append(
			`<section class="past-order-summary">
				<div class="no-summary-placeholder">
					${__('Select an invoice to load summary data')}
				</div>
				<div class="invoice-summary-wrapper">
					<div class="abs-container">
						<div class="upper-section"></div>
						<div class="label">${__('Items')}</div>
						<div class="items-container summary-container"></div>
						<div class="label">${__('Totals')}</div>
						<div class="totals-container summary-container"></div>
						<div class="label">${__('Payments')}</div>
						<div class="payments-container summary-container"></div>
						<div class="summary-btns"></div>
					</div>
				</div>
			</section>`
		);

		this.$component = this.wrapper.find('.past-order-summary');
		this.$summary_wrapper = this.$component.find('.invoice-summary-wrapper');
		this.$summary_container = this.$component.find('.abs-container');
		this.$upper_section = this.$summary_container.find('.upper-section');
		this.$items_container = this.$summary_container.find('.items-container');
		this.$totals_container = this.$summary_container.find('.totals-container');
		this.$payment_container = this.$summary_container.find('.payments-container');
		this.$summary_btns = this.$summary_container.find('.summary-btns');
	}

	init_email_print_dialog() {
		const email_dialog = new frappe.ui.Dialog({
			title: 'Email Receipt',
			fields: [
				{fieldname: 'email_id', fieldtype: 'Data', options: 'Email', label: 'Email ID', reqd: 1},
				{fieldname:'content', fieldtype:'Small Text', label:'Message (if any)'}
			],
			primary_action: () => {
				this.send_email();
			},
			primary_action_label: __('Send'),
		});
		this.email_dialog = email_dialog;

		const print_dialog = new frappe.ui.Dialog({
			title: 'Print Receipt',
			fields: [
				{fieldname: 'print', fieldtype: 'Data', label: 'Print Preview'}
			],
			primary_action: () => {
				this.print_receipt();
			},
			primary_action_label: __('Print'),
		});
		this.print_dialog = print_dialog;
	}

	get_upper_section_html(doc) {
		const { status } = doc;
		let indicator_color = '';

		in_list(['Paid', 'Consolidated'], status) && (indicator_color = 'green');
		status === 'Draft' && (indicator_color = 'red');
		status === 'Return' && (indicator_color = 'grey');

		return `<div class="left-section">
					<div class="customer-name">${doc.customer}</div>
					<div class="customer-email">${this.customer_email}</div>
					<div class="cashier">${__('Sold by')}: ${doc.owner}</div>
				</div>
				<div class="right-section">
					<div class="paid-amount">${format_currency(doc.paid_amount, doc.currency)}</div>
					<div class="invoice-name">${doc.name}</div>
					<span class="indicator-pill whitespace-nowrap ${indicator_color}"><span>${__(doc.status)}</span></span>
				</div>`;
	}

	get_item_html(doc, item_data, packed_items_for_print,type) {


    var htmlContent =`<div class="item-row-wrapper">
		<div class="item-name" style="font-weight: 900;">${item_data.item_name}</div>
		<div class="item-qty" style="font-weight: 900;">${item_data.qty || 0} ${item_data.uom}</div>
		<div class="item-rate-disc" style="font-weight: 900;">${get_rate_discount_html()}</div>
		</div>
		`;

    var modifierHtml='';


		switch (type)
		{
			case "Modifier":
				{
					if(packed_items_for_print)
					{
					 modifierHtml+=`<div class="summary-row-wrapper" style="font-weight: 300;">`;
					 var childrenString='';
					 var is_aded_wthout_childrenString=false;


					 if(doc.custom_without_packed_items.length>0)
					 {
						var custom_without_packed_items=doc.custom_without_packed_items.map(function(item_custom_without_packed_items) {
							if (item_custom_without_packed_items.custom_child_packed_items === item_data.custom_parent_packed_item) {
								return item_custom_without_packed_items;
							}
						 });
						 custom_without_packed_items.forEach(bundle =>{
							var	isChecked = true;
							if(bundle)
							{
								if (bundle.parent_item === item_data.item_code) {
									isChecked =false;
									if(!is_aded_wthout_childrenString)
									{
									  is_aded_wthout_childrenString=true;
									  childrenString+="Without: ("
									}
								   
							 }
							 childrenString += `${!isChecked ?`${bundle.item_code}, `:``}, `; 
							 childrenString=childrenString.replace(/, , /, ", ");
							}
							
							 });
							 if(is_aded_wthout_childrenString)
							 {
								childrenString=childrenString.replace(/, $/, "");
								childrenString+=')<br>'
							 }
					 }
					 
					 childrenString=childrenString.replace(/^,\s*/, '');
					 packed_items_for_print.forEach(item =>{
						childrenString+=`${item.custom_modifier}: (`;
						 
						 item.items.forEach(children=>{
							 childrenString+=`${children.item_code}, `;
						 });
						 childrenString=childrenString.replace(/, $/, "");
						 childrenString+="), ";
						 
					 });
					 childrenString=childrenString.replace(/, $/, "");
					 modifierHtml+=childrenString+'</div>';
					 htmlContent+=modifierHtml;
					}
					break;
				}
			case "Product bundle":
				{
					var is_aded_wthout_childrenString=false;

					if(doc.packed_items)
					{
						modifierHtml+=`<div class="summary-row-wrapper" style="font-weight: 300;">`;
						var childrenString='';
						if(doc.custom_without_packed_items.length>0)
						{

							var custom_without_packed_items=doc.custom_without_packed_items.map(function(item_custom_without_packed_items) {
								if (item_custom_without_packed_items.custom_child_packed_items === item_data.custom_parent_packed_item) {
									return item_custom_without_packed_items;
								}
							 });


							 custom_without_packed_items.forEach(bundle =>{
								var	isChecked = true;
								
								if(bundle)
								{
									if (bundle.parent_item === item_data.item_code) {
										isChecked =false;
										if(!is_aded_wthout_childrenString)
										{
										  is_aded_wthout_childrenString=true;
										  childrenString+="Without: ("
										}
									   
								 }
								 childrenString += `${!isChecked ?`${bundle.item_code}, `:``}, `; 
								 childrenString=childrenString.replace(/, , /, ", ");
								}
								});
						}
						
						childrenString=childrenString.replace(/, $/, "");
						if(is_aded_wthout_childrenString)
						{
						   childrenString=childrenString.replace(/, $/, "");
						   childrenString+=')'
						}
						childrenString=childrenString.replace(/, $/, "");
						modifierHtml+=childrenString+'</div>';
						htmlContent+=modifierHtml;
					}
					break;
				}
		}






       
	  
		return htmlContent;

		
		function get_rate_discount_html() {
			if (item_data.rate && item_data.price_list_rate && item_data.rate !== item_data.price_list_rate) {
				return `<span class="item-disc">(${item_data.discount_percentage}% off)</span>
						<div class="item-rate">${format_currency(item_data.rate, doc.currency)}</div>`;
			} else {
				return `<div class="item-rate">${format_currency(item_data.price_list_rate || item_data.rate, doc.currency)}</div>`;
			}
		}
	}

	get_discount_html(doc) {
		if (doc.discount_amount) {
			return `<div class="summary-row-wrapper">
						<div>${__("Discount")} (${doc.additional_discount_percentage} %)</div>
						<div>${format_currency(doc.discount_amount, doc.currency)}</div>
					</div>`;
		} else {
			return ``;
		}
	}

	get_net_total_html(doc) {
		return `<div class="summary-row-wrapper">
					<div>${__('Net Total')}</div>
					<div>${format_currency(doc.net_total, doc.currency)}</div>
				</div>`;
	}

	async get_taxes_html(doc)   {
		if (!doc.taxes.length) return '';
		let exchange_rate = await this.get_exchange_rate();
		let taxes_html = doc.taxes.map(t => {
			// if tax rate is 0, don't print it.
			const description = /[0-9]+/.test(t.description) ? t.description : ((t.rate != 0) ? `${t.description} @ ${t.rate}%`: t.description);
			let tax_amount_lbp = t.tax_amount_after_discount_amount * exchange_rate; // Convert tax to LBP
			return `
				<div class="tax-row">
					<div class="tax-label">${description}</div>
					<div class="tax-value">${format_currency(t.tax_amount_after_discount_amount, doc.currency)}</div>
					
			<div class="tax-value">${format_currency(tax_amount_lbp, "LBP")}
					</div>
			`;
		}).join('');

		return `<div class="taxes-wrapper">${taxes_html}</div>`;
	}

    async get_grand_total_html(doc) {
        let exchange_rate = await this.get_exchange_rate();
        let grand_total_lbp = doc.grand_total * exchange_rate;

        return `<div class="summary-row-wrapper grand-total">
                    <div>${__('Grand Total (USD)')}</div>
                    <div>${format_currency(doc.grand_total, doc.currency)}</div>
                </div>
                <div class="summary-row-wrapper grand-total">
                    <div>${__('Grand Total (LBP)')}</div>
                    <div>${format_currency(grand_total_lbp, "LBP")}</div>
                </div>`;
    }

	get_payment_html(doc, payment) {
		return `<div class="summary-row-wrapper payments">
					<div>${__(payment.mode_of_payment)}</div>
					<div>${format_currency(payment.amount, doc.currency)}</div>
				</div>`;
	}

	bind_events() {
		this.$summary_container.on('click', '.return-btn', () => {
			this.events.process_return(this.doc.name);
			this.toggle_component(false);
			this.$component.find('.no-summary-placeholder').css('display', 'flex');
			this.$summary_wrapper.css('display', 'none');
		});

		this.$summary_container.on('click', '.edit-btn', () => {
			this.events.edit_order(this.doc.name);
			this.toggle_component(false);
			this.$component.find('.no-summary-placeholder').css('display', 'flex');
			this.$summary_wrapper.css('display', 'none');
		});

		this.$summary_container.on('click', '.delete-btn', () => {
			this.events.delete_order(this.doc.name);
			this.show_summary_placeholder();
		});

		this.$summary_container.on('click', '.delete-btn', () => {
			this.events.delete_order(this.doc.name);
			this.show_summary_placeholder();
			// this.toggle_component(false);
			// this.$component.find('.no-summary-placeholder').removeClass('d-none');
			// this.$summary_wrapper.addClass('d-none');
		});

		this.$summary_container.on('click', '.new-btn', () => {
			this.events.new_order();
			this.toggle_component(false);
			this.$component.find('.no-summary-placeholder').css('display', 'flex');
			this.$summary_wrapper.css('display', 'none');
		});

		this.$summary_container.on('click', '.email-btn', () => {
			this.email_dialog.fields_dict.email_id.set_value(this.customer_email);
			this.email_dialog.show();
		});

		this.$summary_container.on('click', '.print-btn', () => {
			this.print_receipt();
		});
	}

	print_receipt() {
		const frm = this.events.get_frm();
		frappe.utils.print(
			this.doc.doctype,
			this.doc.name,
			frm.pos_print_format,
			this.doc.letter_head,
			this.doc.language || frappe.boot.lang
		);
	}

	attach_shortcuts() {
		const ctrl_label = frappe.utils.is_mac() ? '⌘' : 'Ctrl';
		this.$summary_container.find('.print-btn').attr("title", `${ctrl_label}+P`);
		frappe.ui.keys.add_shortcut({
			shortcut: "ctrl+p",
			action: () => this.$summary_container.find('.print-btn').click(),
			condition: () => this.$component.is(':visible') && this.$summary_container.find('.print-btn').is(":visible"),
			description: __("Print Receipt"),
			page: cur_page.page.page
		});
		this.$summary_container.find('.new-btn').attr("title", `${ctrl_label}+Enter`);
		frappe.ui.keys.on("ctrl+enter", () => {
			const summary_is_visible = this.$component.is(":visible");
			if (summary_is_visible && this.$summary_container.find('.new-btn').is(":visible")) {
				this.$summary_container.find('.new-btn').click();
			}
		});
		this.$summary_container.find('.edit-btn').attr("title", `${ctrl_label}+E`);
		frappe.ui.keys.add_shortcut({
			shortcut: "ctrl+e",
			action: () => this.$summary_container.find('.edit-btn').click(),
			condition: () => this.$component.is(':visible') && this.$summary_container.find('.edit-btn').is(":visible"),
			description: __("Edit Receipt"),
			page: cur_page.page.page
		});
	}

	send_email() {
		const frm = this.events.get_frm();
		const recipients = this.email_dialog.get_values().email_id;
		const content = this.email_dialog.get_values().content;
		const doc = this.doc || frm.doc;
		const print_format = frm.pos_print_format;

		frappe.call({
			method: "frappe.core.doctype.communication.email.make",
			args: {
				recipients: recipients,
				subject: __(frm.meta.name) + ': ' + doc.name,
				content: content ? content : __(frm.meta.name) + ': ' + doc.name,
				doctype: doc.doctype,
				name: doc.name,
				send_email: 1,
				print_format,
				sender_full_name: frappe.user.full_name(),
				_lang: doc.language
			},
			callback: r => {
				if (!r.exc) {
					frappe.utils.play_sound("email");
					if (r.message["emails_not_sent_to"]) {
						frappe.msgprint(__(
							"Email not sent to {0} (unsubscribed / disabled)",
							[ frappe.utils.escape_html(r.message["emails_not_sent_to"]) ]
						));
					} else {
						frappe.show_alert({
							message: __('Email sent successfully.'),
							indicator: 'green'
						});
					}
					this.email_dialog.hide();
				} else {
					frappe.msgprint(__("There were errors while sending email. Please try again."));
				}
			}
		});
	}

	add_summary_btns(map) {
		this.$summary_btns.html('');
		map.forEach(m => {
			if (m.condition) {
				m.visible_btns.forEach(b => {
					const class_name = b.split(' ')[0].toLowerCase();
					const btn = __(b);
					this.$summary_btns.append(
						`<div class="summary-btn btn btn-default ${class_name}-btn">${btn}</div>`
					);
				});
			}
		});
		this.$summary_btns.children().last().removeClass('mr-4');
	}

	toggle_summary_placeholder(show) {
		if (show) {
			this.$summary_wrapper.css('display', 'none');
			this.$component.find('.no-summary-placeholder').css('display', 'flex');
		} else {
			this.$summary_wrapper.css('display', 'flex');
			this.$component.find('.no-summary-placeholder').css('display', 'none');
		}
	}

	get_condition_btn_map(after_submission) {
		if (after_submission)
			return [{ condition: true, visible_btns: ['Print Receipt', 'Email Receipt', 'New Order'] }];

		return [
			{ condition: this.doc.docstatus === 0, visible_btns: ['Edit Order', 'Delete Order'] },
			{ condition: !this.doc.is_return && this.doc.docstatus === 1, visible_btns: ['Print Receipt', 'Email Receipt', 'Return']},
			{ condition: this.doc.is_return && this.doc.docstatus === 1, visible_btns: ['Print Receipt', 'Email Receipt']}
		];
	}

	load_summary_of(doc, after_submission=false) {
		after_submission ?
			this.$component.css('grid-column', 'span 10 / span 10') :
			this.$component.css('grid-column', 'span 6 / span 6');

		this.toggle_summary_placeholder(false);

		this.doc = doc;

		this.attach_document_info(doc);

		this.attach_items_info(doc);

		this.attach_totals_info(doc);

		this.attach_payments_info(doc);

		const condition_btns_map = this.get_condition_btn_map(after_submission);

		this.add_summary_btns(condition_btns_map);

		if (after_submission) {
			this.print_receipt_on_order_complete();
		}
	}

	attach_document_info(doc) {
		frappe.db.get_value('Customer', this.doc.customer, 'email_id').then(({ message }) => {
			this.customer_email = message.email_id || '';
			const upper_section_dom = this.get_upper_section_html(doc);
			this.$upper_section.html(upper_section_dom);
		});
	}

	attach_items_info(doc) {
		this.$items_container.html('');
		
		doc.items.forEach(item => {
			var type = "";
			var  packed_items_for_print=[];
			if(doc.packed_items)
			{
				console.log('ssssss');
				var packed_items_for_item=doc.packed_items.map(function(item_doc_packed_items) {
					if ((item_doc_packed_items.parent_item === item.item_code &&  item_doc_packed_items.custom_child_packed_items===item.custom_parent_packed_item) || item_doc_packed_items.custom_child_packed_items===item.custom_parent_packed_item) {
						return item_doc_packed_items;
					}
				 });
				 var is_packed_items_for_item =false;
				 

				 for (let i = 0; i < packed_items_for_item.length; i++) {
					
					if (packed_items_for_item[i]?.custom_modifier) {
						is_packed_items_for_item=true;
						break; 
					}
				}
				 if(packed_items_for_item.length>0 && is_packed_items_for_item)
				 {
					type="Modifier";
					packed_items_for_print =this.groupItemsByModifier(packed_items_for_item);
				 }
				 else
				 {
					type="Product bundle"; 
				 }
			}
			const item_dom = this.get_item_html(doc, item, packed_items_for_print,type);
			this.$items_container.append(item_dom);
			this.set_dynamic_rate_header_width();
		});
	}

	 groupItemsByModifier(items) {
		// Create an object to hold the grouped items
		const groupedItems = {};
	  
		// Iterate over each item in the input array
		items.forEach(item => {
			if(item && item.custom_modifier)
			{
				const modifier = item.custom_modifier; // Get the custom_modifier value of the item
	  
				// If the modifier does not exist in the groupedItems, create an empty array for it
				if (!groupedItems[modifier]) {
				  groupedItems[modifier] = [];
				}
			
				// Push the current item into the array corresponding to its modifier
				groupedItems[modifier].push(item);
			}
		 
		});
	  
		// Convert the grouped items object into an array of groups
		const groupedArray = Object.entries(groupedItems).map(([modifier, items]) => ({
		  custom_modifier: modifier,
		  items: items
		}));
	  
		return groupedArray;
	  }

	set_dynamic_rate_header_width() {
		const rate_cols = Array.from(this.$items_container.find(".item-rate-disc"));
		this.$items_container.find(".item-rate-disc").css("width", "");
		let max_width = rate_cols.reduce((max_width, elm) => {
			if ($(elm).width() > max_width)
				max_width = $(elm).width();
			return max_width;
		}, 0);

		max_width += 1;
		if (max_width == 1) max_width = "";

		this.$items_container.find(".item-rate-disc").css("width", max_width);
	}

	attach_payments_info(doc) {
		this.$payment_container.html('');
		doc.payments.forEach(p => {
			if (p.amount) {
				const payment_dom = this.get_payment_html(doc, p);
				this.$payment_container.append(payment_dom);
			}
		});
		if (doc.redeem_loyalty_points && doc.loyalty_amount) {
			const payment_dom = this.get_payment_html(doc, {
				mode_of_payment: 'Loyalty Points',
				amount: doc.loyalty_amount,
			});
			this.$payment_container.append(payment_dom);
		}
	}

	async attach_totals_info(doc) {
		this.$totals_container.html('');

		const net_total_dom = this.get_net_total_html(doc);
		const taxes_dom = await this.get_taxes_html(doc);
		const discount_dom = this.get_discount_html(doc);
		const grand_total_dom = await this.get_grand_total_html(doc);
		this.$totals_container.append(net_total_dom);
		this.$totals_container.append(taxes_dom);
		this.$totals_container.append(discount_dom);
		this.$totals_container.append(grand_total_dom);
	}



    async get_exchange_rate() {
        let exchange_rate = 89000; // Default rate

        try {
            const res = await frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Currency Exchange",
                    filters: {
                        from_currency: "USD",
                        to_currency: "LBP"
                    },
                    fields: ["exchange_rate"],
                    order_by: "modified desc", 
                    limit_page_length: 1
                }
            });

            if (res && res.message.length > 0) {
                exchange_rate = res.message[0].exchange_rate;
            }
        } catch (error) {
            console.error("Error fetching exchange rate:", error);
        }

        return exchange_rate;
    }

	toggle_component(show) {
		show ? this.$component.css('display', 'flex') : this.$component.css('display', 'none');
	}

	async print_receipt_on_order_complete() {
		const res = await frappe.db.get_value(
			"POS Profile",
			this.pos_profile,
			"print_receipt_on_order_complete"
		);

		if (res.message.print_receipt_on_order_complete) {
			this.print_receipt();
		}
	}
};
