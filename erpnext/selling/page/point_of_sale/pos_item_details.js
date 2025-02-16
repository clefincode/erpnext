erpnext.PointOfSale.ItemDetails = class {
	constructor({ wrapper, events, settings }) {
		this.wrapper = wrapper;
		this.events = events;
		this.hide_images = settings.hide_images;
		this.allow_rate_change = settings.allow_rate_change;
		this.allow_discount_change = settings.allow_discount_change;
		this.current_item = {};
		this.is_coupon_available=true;
		this.init_component();
	}

	init_component() {
		this.prepare_dom();
		this.init_child_components();
		this.bind_events();
		this.attach_shortcuts();
	}

	prepare_dom() {
		this.wrapper.append(
			`<section class="item-details-container" >
			</section>`
		)

		this.$component = this.wrapper.find('.item-details-container');
		
		
	}

	init_child_components() {
		
		this.$component.html(
			`<div class="item-details-header">
				<div class="label">${__('Item Details')}</div>
				<div class="close-btn">
					<svg width="32" height="32" viewBox="0 0 14 14" fill="none">
						<path d="M4.93764 4.93759L7.00003 6.99998M9.06243 9.06238L7.00003 6.99998M7.00003 6.99998L4.93764 9.06238L9.06243 4.93759" stroke="#8D99A6"/>
					</svg>
				</div>
			</div>
			<div class="item-display">
				<div class="item-name-desc-price">
					<div class="item-name"></div>
					<div class="item-desc"></div>
					<div class="item-price"></div>
				</div>
				<div class="item-image"></div>
			</div>
			<div class="discount-section"></div>
			<div class="form-container"></div>
			<div class="discount-section"></div>
			<div class="bundle_components"></div>
			<div class="discount-section"></div>
			<div class="modifiers_components"></div>
			<div class="serial-batch-container"></div>`
		)

		this.$item_name = this.$component.find('.item-name');
		this.$item_description = this.$component.find('.item-desc');
		this.$item_price = this.$component.find('.item-price');
		this.$item_image = this.$component.find('.item-image');
		this.$form_container = this.$component.find('.form-container');
		this.$bundle_components = this.$component.find('.bundle_components');
		this.$modifiers_components = this.$component.find('.modifiers_components');
		this.$dicount_section = this.$component.find('.discount-section');
		this.$serial_batch_container = this.$component.find('.serial-batch-container');
	}

	compare_with_current_item(item) {
		// returns true if `item` is currently being edited
		return item && item.name == this.current_item.name;
	}

	async toggle_item_details_section(item) {
		const current_item_changed = !this.compare_with_current_item(item);

		// if item is null or highlighted cart item is clicked twice
		const hide_item_details = !Boolean(item) || !current_item_changed;

		if ((!hide_item_details && current_item_changed) || hide_item_details) {
			// if item details is being closed OR if item details is opened but item is changed
			// in both cases, if the current item is a serialized item, then validate and remove the item
			await this.validate_serial_batch_item();
		}

		this.events.toggle_item_selector(!hide_item_details);
		this.toggle_component(!hide_item_details);

		if (item && current_item_changed) {
			this.doctype = item.doctype;
			this.item_meta = frappe.get_meta(this.doctype);
			this.name = item.name;
			this.item_row = item;
			this.currency = this.events.get_frm().doc.currency;
			this.current_item = item;
			const container = $('.bundle_components');
			container.html("");
			const modifiers_components = $('.modifiers_components');
			modifiers_components.html("");
			this.render_dom(item);
			this.render_discount_dom(item);
			this.render_form(item);
			this.product_bundle(item);
			this.modifiers(item);
			this.events.highlight_cart_item(item);
		} else {
			this.current_item = {};
		}
	}

	validate_serial_batch_item() {
		const doc = this.events.get_frm().doc;
		const item_row = doc.items.find(item => item.name === this.name);

		if (!item_row) return;

		const serialized = item_row.has_serial_no;
		const batched = item_row.has_batch_no;
		const no_bundle_selected =
			!item_row.serial_and_batch_bundle && !item_row.serial_no && !item_row.batch_no;

		if ((serialized && no_bundle_selected) || (batched && no_bundle_selected)) {
			frappe.show_alert({
				message: __("Item is removed since no serial / batch no selected."),
				indicator: 'orange'
			});
			frappe.utils.play_sound("cancel");
			return this.events.remove_item_from_cart();
		}
	}

	render_dom(item) {
		let { item_name, description, image, price_list_rate } = item;

		function get_description_html() {
			if (description) {
				description = description.indexOf('...') === -1 && description.length > 140 ? description.substr(0, 139) + '...' : description;
				return description;
			}
			return ``;
		}

		this.$item_name.html(item_name);
		this.$item_description.html(get_description_html());
		this.$item_price.html(format_currency(price_list_rate, this.currency));
		if (!this.hide_images && image) {
			this.$item_image.html(
				`<img
					onerror="cur_pos.item_details.handle_broken_image(this)"
					class="h-full" src="${image}"
					alt="${frappe.get_abbr(item_name)}"
					style="object-fit: cover;">`
			);
		} else {
			this.$item_image.html(`<div class="item-abbr">${frappe.get_abbr(item_name)}</div>`);
		}

	}

	handle_broken_image($img) {
		const item_abbr = $($img).attr('alt');
		$($img).replaceWith(`<div class="item-abbr">${item_abbr}</div>`);
	}

	render_discount_dom(item) {
		if (item.discount_percentage) {
			this.$dicount_section.html(
				`<div class="item-rate">${format_currency(item.price_list_rate, this.currency)}</div>
				<div class="item-discount">${item.discount_percentage}% off</div>`
			)
			this.$item_price.html(format_currency(item.rate, this.currency));
		} else {
			this.$dicount_section.html(``)
		}
	}

	render_form(item) {
		const fields_to_display = this.get_form_fields(item);
		this.$form_container.html('');

		fields_to_display.forEach((fieldname, idx) => {
			this.$form_container.append(
				`<div class="${fieldname}-control" data-fieldname="${fieldname}"></div>`
			)

			const field_meta = this.item_meta.fields.find(df => df.fieldname === fieldname);
			fieldname === 'discount_percentage' ? (field_meta.label = __('Discount (%)')) : '';
			const me = this;

			this[`${fieldname}_control`] = frappe.ui.form.make_control({
				df: {
					...field_meta,
					onchange: function() {

						if(fieldname=='qty' )
						{
							const doc = me.events.get_frm().doc;
							if(doc.active_coupon)
							{
								
								var response =  validateCoupon(doc.grand_total ? (parseFloat(doc.grand_total - me.current_item.base_net_amount)) + parseFloat(me.current_item.base_amount * this.value) : parseFloat(me.current_item.base_price_list_rate) , doc.card_value, me , {fieldname : fieldname} )
								if(response.error)
								{
									frappe.msgprint(__(response.error));
									
									return ;
								}
								else
								{
									
								}
							}
						
							
						}
						else
						{
							me.events.form_updated(me.current_item, fieldname, this.value);
						}
					
						
					
						
					}
					
				},
				parent: this.$form_container.find(`.${fieldname}-control`),
				render_input: true,
			});
			this[`${fieldname}_control`].set_value(item[fieldname]);
			
		});

		this.make_auto_serial_selection_btn(item);

		this.bind_custom_control_change_event();

		function validateCoupon(invoiceValue, cardValue ,me , { fieldname=null }) {
			const doc = me.events.get_frm().doc;
			invoiceValue = ( invoiceValue - ((doc.discount_percentage / 100) * invoiceValue));
			if(invoiceValue > cardValue && invoiceValue - cardValue >= 1)
			{
				doc.is_coupon_available=false;
				me.is_coupon_available=false;
				
			}
			else
			{
				doc.is_coupon_available=true;
				me.is_coupon_available=true;
			}

			if (cardValue >= invoiceValue || me.is_coupon_available) {
			  return {
				success: true
			  };
			} else {
				if(fieldname)
				{
					me[`${fieldname}_control`].set_value(item[fieldname]);
				}
			  return {
				error: `The invoice value ${invoiceValue} is greater than the coupon balance ${cardValue}. Please complete the order before adding any new items.`
			};
			}
		  }
	}


	product_bundle(item) {
		const me = this;
		var custom_has_modifier =false;
		var data_item_response = [];
		frappe.db.exists('Product Bundle', item.item_code)
        .then(exists => {
            if (exists) {
				frappe.db.get_value('Item', { 'item_code': item.item_code }, "custom_has_modifier")
				.then(res => {
					custom_has_modifier=res.message.custom_has_modifier;
					if (res.message && !res.message.custom_has_modifier) {
						document.querySelectorAll('.bundle-components').forEach(div => {
							div.style.minHeight = '100%';
							div.style.height = '100%';
							div.style.overflowY = 'auto';
							div.style.padding = '4px 0px 1rem 0px';
						});
						this.$component = this.wrapper.find('.item-details-container');
						this.$component.css({
							'max-height': 'none',
							'height': 'auto',
							'min-height': 'auto'
						});
					}
					else
					{
						document.querySelectorAll('.bundle-components').forEach(div => {
							div.style.minHeight = '100%';
							div.style.height = '100%';
							div.style.overflowY = 'auto';
							div.style.padding = '4px 0px 1rem 0px';
						});
						
					}
				});
				frappe.call({
					method: "sultan_1975.api.api.get_bundle_items",
					args: {
						item_code: item.item_code
					},
					callback: function(response) {
						
						if (response.message) {
							var data_item = [];
							data_item_response = [...response.message];
							if (item.packed_items != null && item.packed_items.length > 0) {
								var packed_items_data_item =[];
								
								response.message.forEach(item_response =>{
									var find_index =item.packed_items.findIndex(item => item.item_code === item_response.item_code);
									
										if(find_index==-1 )
										{
										item_response.isChecked=false;
										packed_items_data_item.push(item_response);
									}
									else{
										item.packed_items[find_index].isChecked=true;
										packed_items_data_item.push(item.packed_items[find_index]);
									}
									});
							
								data_item=[...packed_items_data_item];
							} else {
								data_item = [...response.message];
							}
							const container = $('.bundle_components');
							container.html("");
							let htmlContent = `
								<div class="label">Bundle Components</div>
								<div class="discount-section" style="margin-bottom: var(--margin-sm);"></div>
								<div class="bundle-components" style="height: ${!custom_has_modifier? "100%;":"100%;"} min-height: ${!custom_has_modifier? "100%;":"100%;"} overflow-y: auto; padding: 4px 0px 1rem 0px;">
									<ul style="padding: 0; margin: 0; list-style: none;">
							`;
							// Generate the HTML content for the items
							data_item.forEach(function(bundle_item) {

								var	isChecked = true;
								if (item.packed_items != null && item.packed_items.length > 0) {
									if(item.custom_without_packed_items != null && item.custom_without_packed_items.length > 0)
									{
										var find_index =item.custom_without_packed_items.findIndex(without => without.item_code === bundle_item.item_code);
										if(find_index!==-1)
										{
										   isChecked =false;
										}
									}
									
								}
							
								//<span  style=" ${!isChecked ? 'text-decoration:var(--red-500) line-through;' : ''} flex: 1; text-align: left;">${bundle_item.price}</span>
								htmlContent += `
									<li class ="bundle-item" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; margin-right: 10px;">
										<span  style=" ${!isChecked ? 'text-decoration:var(--red-500) line-through;' : ''} flex: 2; text-align: left;">${bundle_item.item_code}</span>
										<span  style=" ${!isChecked ? 'text-decoration:var(--red-500) line-through;' : ''} flex: 1; text-align: left;">${bundle_item.uom}</span>
										
										<button class="decrease-btn-product-bundle"  ${isChecked ? '' : 'disabled'} data-item-code="${bundle_item.item_code}" data-price="${bundle_item.price}" style="
										border-radius: var(--border-radius-sm);
										display: flex;
										align-items: center;
										justify-content: center;
										padding: 0px 11px;
										box-shadow: var(--shadow-md);
										border: none;
										font-size: var(--text-2xl);
										background-color: transparent;">-</button>
										<input type="number" ${isChecked ? '' : 'readonly'} class="qty-input-product-bundle" value="${bundle_item.qty}" data-item-code="${bundle_item.item_code}" style="width: 50px; background-color: var(--control-bg); text-align: center; margin: 0 10px; border: none; border-radius: 5px;" />
										<button class="increase-btn-product-bundle" ${isChecked ? '' : 'disabled'} data-item-code="${bundle_item.item_code}" data-price="${bundle_item.price}" style="
										border-radius: var(--border-radius-sm);
										display: flex;
										align-items: center;
										justify-content: center;
										padding: 0px 11px;
										box-shadow: var(--shadow-md);
										border: none;
										font-size: var(--text-xl);
										margin-right: 20px;
										background-color: transparent;">+</button>
										<input type="checkbox" class="select-item-product-bundle" data-item-code="${bundle_item.item_code}" data-price="${bundle_item.price}" data-qty="${bundle_item.qty}" ${isChecked ? 'checked' : ''} style="
										margin-right: 20px;"}>
									</li>
								`;
							});
						
							htmlContent += `
									</ul>
								</div>
							`;
						
							container.append(htmlContent);
						
							// Handle checkbox click
							$('.select-item-product-bundle').change(function() {
								const itemCode = $(this).data('item-code');
    							const inputField = $(`.qty-input-product-bundle[data-item-code="${itemCode}"]`).val();
    							const inputField_update = $(`.qty-input-product-bundle[data-item-code="${itemCode}"]`);
    							const price = $(this).data('price');
    							const listItem = $(this).closest('.bundle-item');
    							const increaseBtn = listItem.find('.increase-btn-product-bundle');
    							const decreaseBtn = listItem.find('.decrease-btn-product-bundle');
    							const qtyInput = listItem.find('.qty-input-product-bundle');
    							const textSpans = listItem.find('span');
						    	var quantity =inputField;
								listItem.css({
									'transition': 'all 0.3s ease', // Add transition for smooth effect
								});
								if ($(this).is(':checked')) {
							
									if (inputField == 0) {
										inputField_update.val(1);
										updatePackedItems(itemCode, 1);
									}
									else{
										updatePackedItems(itemCode, parseFloat(quantity));
									}
									textSpans.css('text-decoration', 'none');
									 // Remove strike-through
									increaseBtn.prop('disabled', false); // Enable buttons
									decreaseBtn.prop('disabled', false); 
									qtyInput.prop('readonly', false); // Make input editable
									const inputElement = document.querySelector('.rate-control .control-input input');
									const rate = parseFloat(parseFloat(inputElement.value.toString().replace(',', '')).toFixed(2));
									if(inputField>1)
									{
										const max =rate + ((inputField >1 ? inputField-1 : inputField) * parseFloat(price));
										//updateRate(max);
									}
									else{
										const max =rate + (1 * parseFloat(price));
										//updateRate(max);
									}
									
									
									
								} else {
									textSpans.css('text-decoration', 'var(--red-500) line-through');
									increaseBtn.prop('disabled', true); // Disable buttons
									decreaseBtn.prop('disabled', true); 
									qtyInput.prop('readonly', true); // Make input read-only
								}
						
								// Handle removal from packed_items if unchecked
								if (!$(this).is(':checked')) {
	
									var without_packaged_items =[];


									
									var data = [];
									if (item.packed_items != null && item.packed_items.length > 0) {
										var packed_items_data_item =[];
									
									data_item_response.forEach(item_response =>{
										var find_index =item.packed_items.findIndex(item => item.item_code === item_response.item_code);
										var find_index_without =-1;
										if(item.custom_without_packed_items)
										{
											find_index_without =item.custom_without_packed_items.findIndex(item => item.item_code === item_response.item_code);
										}
										if(find_index==-1 )
										{
											if(find_index_without==-1)
											{
												item_response.isChecked=false;
												packed_items_data_item.push(item_response);
											
											}
										}
										else{
											item.packed_items[find_index].isChecked=true;
											packed_items_data_item.push(item.packed_items[find_index]);
										}
										});
								
									data_item=[...packed_items_data_item];
									}
									

									if(inputField>1)
									{
										const inputElement = document.querySelector('.rate-control .control-input input');
										const rate = parseFloat(parseFloat(inputElement.value.toString().replace(',', '')).toFixed(2));
										var max =0;
										if (item.packed_items != null && item.packed_items.length > 0) {
											data_item = item.packed_items;
										}
										const item_find = data_item.find(item => item.item_code === itemCode);
										if(item_find)
										{
											if(quantity>item_find.qty)
											{
												max =rate + ((inputField >1 ? inputField-1 : inputField) * parseFloat(price));
											}
											else if(quantity<item_find.qty) {
												max =rate - ((inputField >1 ? inputField-1 : inputField) * parseFloat(price));
											}
											else{
												max =rate - ((quantity-1) * parseFloat(price));
											}
										}
										else{
											max =rate - ((inputField >1 ? inputField-1 : inputField) * parseFloat(price));
										}
										//updateRate(max);
										
									}
									
									if(inputField==1)
									{
										const inputElement = document.querySelector('.rate-control .control-input input');
										const rate = parseFloat(parseFloat(inputElement.value.toString().replace(',', '')).toFixed(2));
										var max =0;
										max =rate - (1 * parseFloat(price));
										//updateRate(max);
									}
									data = data_item.filter(function(d_tem) {
										if(item.packed_items != null && item.packed_items.length > 0)
										{
											if(d_tem.item_code !== itemCode &&  d_tem.isChecked)
											{
												return item;
											}
										}
										else{
											if(d_tem.item_code !== itemCode )
											{
												return item;
											}	
										}
										
									 
								   });
								   data_item_response.forEach(item_response =>{
									var find_index =data.findIndex(item => item.item_code === item_response.item_code);
									if(find_index==-1)
									{
										without_packaged_items.push(item_response);
										
									}
									else{
									var find_index =without_packaged_items.findIndex(item => item.item_code === item_response.item_code);
									if(find_index!==-1)
									{
										without_packaged_items.splice(find_index, 1);
										
									}
									}
									});
								   
								me.events.form_updated(me.current_item, 'packed_items', data,);
									me.events.form_updated_without_packed_items(me.current_item, 'custom_without_packed_items', without_packaged_items);
								}
							});
						
							// Handle increase button click
							$('.increase-btn-product-bundle').click(function() {
							
								const itemCode = $(this).data('item-code');
								const price = $(this).data('price');
								const inputField = $(`.qty-input-product-bundle[data-item-code="${itemCode}"]`);
								let quantity = parseInt(inputField.val()) || 1;
								quantity += 1;
								inputField.val(quantity);
								
								updatePackedItems(itemCode, quantity);
						
								const inputElement = document.querySelector('.rate-control .control-input input');
								const rate = parseFloat(parseFloat(inputElement.value.toString().replace(',', '')).toFixed(2));
								const max = rate + (1 * parseFloat(price));
								//updateRate(max);
							});
						
							// Handle decrease button click
							$('.decrease-btn-product-bundle').click(function() {
								const itemCode = $(this).data('item-code');
								const price = $(this).data('price');
								const inputField = $(`.qty-input-product-bundle[data-item-code="${itemCode}"]`);
								let quantity = parseInt(inputField.val()) || 1;
								if (quantity > 1) {
									quantity -= 1;
									inputField.val(quantity);
									updatePackedItems(itemCode, quantity);
									const inputElement = document.querySelector('.rate-control .control-input input');
									const rate = parseFloat(parseFloat(inputElement.value.toString().replace(',', '')).toFixed(2));
									const max = rate - (1 * parseFloat(price));
									//updateRate(max);
								}
						
								// Strike through the element if quantity is 0
								if (quantity === 0) {
									const listItem = $(this).closest('.bundle-item');
									const textSpans = listItem.find('span');
									textSpans.css('text-decoration', 'var(--red-500)  line-through');
								}
							});
							let oldValue=0;
							$('.qty-input-product-bundle').each(function () {
                                 oldValue = $(this).val(); 

                                $(this).on('focus', function () {
                                    oldValue = $(this).val(); 
                                });
                            });
				
							$('.qty-input-product-bundle').change(function() {
								const itemCode = $(this).data('item-code');
								let quantity = parseInt($(this).val());

								if(quantity === 0 || quantity < 1)
								{
									var without_packaged_items =[];
									const itemCode = $(this).data('item-code');
									const inputField = $(`.qty-input-product-bundle[data-item-code="${itemCode}"]`).val();
									const inputField_update = $(`.qty-input-product-bundle[data-item-code="${itemCode}"]`);
									const price = $(this).data('price');
									const listItem = $(this).closest('.bundle-item');
               						listItem.find('.select-item').prop('checked', false);
									const increaseBtn = listItem.find('.increase-btn-product-bundle');
									const decreaseBtn = listItem.find('.decrease-btn-product-bundle');
									const qtyInput = listItem.find('.qty-input-product-bundle');
									const textSpans = listItem.find('span');
									textSpans.css('text-decoration', 'var(--red-500)  line-through');
									increaseBtn.prop('disabled', true); // Disable buttons
									decreaseBtn.prop('disabled', true); 
									qtyInput.prop('readonly', true); 
									var data = [];
									if (item.packed_items != null && item.packed_items.length > 0) {
										var packed_items_data_item =[];
									
									data_item_response.forEach(item_response =>{
										var find_index =item.packed_items.findIndex(item => item.item_code === item_response.item_code);
										var find_index_without =-1;
										 if(item.custom_without_packed_items)
										 {
											find_index_without =item.custom_without_packed_items.findIndex(item => item.item_code === item_response.item_code);
										 }
										 if(find_index==-1 )
										 {
											 if(find_index_without==-1)
											 {
												item_response.isChecked=false;
												 packed_items_data_item.push(item_response);
												
											 }
										 }
										else{
											item.packed_items[find_index].isChecked=true;
											packed_items_data_item.push(item.packed_items[find_index]);
										}
										});
								
									data_item=[...packed_items_data_item];
									}
								
									if(inputField>=1)
									{
										const inputElement = document.querySelector('.rate-control .control-input input');
										const rate = parseFloat(parseFloat(inputElement.value.toString().replace(',', '')).toFixed(2));
										var max =0;
										const item = data_item.find(item => item.item_code === itemCode);
										if(item)
										{
											if(quantity>item.qty)
											{
												max =rate + ((inputField >1 ? inputField-1 : inputField) * parseFloat(price));
											}
											else if(quantity<item.qty) {
												max =rate - ((inputField >1 ? inputField-1 : inputField) * parseFloat(price));
											}
											else{
												max =rate - ((quantity-1) * parseFloat(price));
											}
										}
										else{
											max =rate + ((inputField >1 ? inputField-1 : inputField) * parseFloat(price));
										}
										//updateRate(max);
									}
									else
									{

										inputField_update.val(1);
									}
									data = data_item.filter(function(d_tem) {
										if(item.packed_items != null && item.packed_items.length > 0)
										{
											if(d_tem.item_code !== itemCode &&  !d_tem.isChecked)
											{
												return item;
											}
										}
										else{
											if(d_tem.item_code !== itemCode )
											{
												return item;
											}	
										}
										
									 
								   });
								   
								   data_item_response.forEach(item_response =>{
									var find_index =data.findIndex(item => item.item_code === item_response.item_code);
									if(find_index==-1)
									{
										without_packaged_items.push(item_response);
										
									}
									else{
										var find_index =without_packaged_items.findIndex(item => item.item_code === item_response.item_code);
										if(find_index!==-1)
										{
											without_packaged_items.splice(find_index, 1);
											
										}
										}
									});
								   
								me.events.form_updated(me.current_item, 'packed_items', data,);
								
								
									me.events.form_updated_without_packed_items(me.current_item, 'custom_without_packed_items', without_packaged_items);
								
								}
							
								else{
									const inputElement = document.querySelector('.rate-control .control-input input');
									const rate = parseFloat(parseFloat(inputElement.value.toString().replace(',', '')).toFixed(2));
									var max =0;
									if (item.packed_items != null && item.packed_items.length > 0) {
										var packed_items_data_item =[];
									
									data_item_response.forEach(item_response =>{
										var find_index =item.packed_items.findIndex(item => item.item_code === item_response.item_code);
										var find_index_without =-1;
										if(item.custom_without_packed_items)
										{
										   find_index_without =item.custom_without_packed_items.findIndex(item => item.item_code === item_response.item_code);
										}
										if(find_index==-1 )
										{
											if(find_index_without==-1)
											{
												item_response.isChecked=false;
												packed_items_data_item.push(item_response);
												
											}
										}
										else{
											item.packed_items[find_index].isChecked=true;
											packed_items_data_item.push(item.packed_items[find_index]);
										}
										});
								
									data_item=[...packed_items_data_item];
									}
									const item_find = data_item.find(item => item.item_code === itemCode);
								
									var price=0; 
									if(item_find) 
									{
										price = parseFloat(item_find.price);
										
										if(quantity>item_find.qty)
										{
											max = rate+((quantity-item.qty) * parseFloat(price));
										}
										else if(quantity<item_find.qty) {
											max = rate-((item_find.qty-quantity) * parseFloat(price));
										}
										else{
											// max =rate - (1 * parseFloat(price));
										}
									}
									else{
										const item_find = response.message.find(item => item.item_code === itemCode);
										price=parseFloat(item_find.price);
										max = rate+((quantity-oldValue) * parseFloat(price));
									}
									//updateRate(max);
								}
						
								updatePackedItems(itemCode, quantity,(quantity === 0 || quantity < 1));
							});
						
							// Update packed_items and trigger the form update event
							function updatePackedItems(itemCode, quantity ,without=false) {
								var without_packaged_items =[];
								if (item.packed_items != null && item.packed_items.length > 0) {
									var packed_items_data_item =[];
								
								data_item_response.forEach(item_response =>{
									var find_index =item.packed_items.findIndex(item => item.item_code === item_response.item_code);
									var find_index_without =-1;
									if(item.custom_without_packed_items)
									{
									   find_index_without =item.custom_without_packed_items.findIndex(item => item.item_code === item_response.item_code);
									}									
									if(without)
									{
										without_packaged_items.push(item_response);
									}
									else
									{


										if(find_index==-1 )
										{
											if(find_index_without==-1)
											{
												item_response.isChecked=false;
												packed_items_data_item.push(item_response);
												without_packaged_items.push(item_response);
											}
										}
										
										else{
											item.packed_items[find_index].isChecked=true;
											packed_items_data_item.push(item.packed_items[find_index]);
										}
									}
									
									
									});
							
								data_item=[...packed_items_data_item];
								}
								var data = [];
								data = data_item.map(function(item) {
									if (item.item_code === itemCode) {
										return { item_code: item.item_code, qty: quantity, uom: item.uom, price: item.price };
									}
									return item;
								});
						
								me.events.form_updated(me.current_item, 'packed_items', data );
								
								if(item.custom_without_packed_items)
								{

									without_packaged_items= item.custom_without_packed_items.filter(
										(currentItem) => currentItem.item_code !== itemCode
									  );
									  me.events.form_updated_without_packed_items(me.current_item, 'custom_without_packed_items', without_packaged_items);
								}
					
							}
						
							// Update rate and trigger the form update event
							function updateRate(max) {
								
								me.events.form_updated(me.current_item, 'rate', max).then(() => {
									const item_row = frappe.get_doc(me.doctype, me.current_item.name);
									const doc = me.events.get_frm().doc;
									me.$item_price.html(format_currency(item_row.rate, doc.currency));
									me.render_discount_dom(item_row);
								});
							}
						}
						
					
					},
					error: function(error) {
						console.error("An error occurred: ", error);
					}
				});
            }
        }).catch(err => {
            console.error('Error checking existence of product bundle:', err);
            frappe.msgprint(__('Failed to check if item is a product bundle: ' + item));
        });
	}

	
	modifiers(item) {
		
		const me = this;
		var data_option_response = [];
		let  item_is_Checked =[];
		frappe.db.get_value('Item', { 'item_code': item.item_code }, "custom_has_modifier")
			.then(res => {
				if (res.message && res.message.custom_has_modifier) {
					this.$component = this.wrapper.find('.item-details-container');
					this.$component.css({
						'max-height': 'none',
						'height': 'auto',
						'min-height': 'auto'
					});
					const container = $('.modifiers_components');
					container.html("");
					let htmlContent = `
						<div class="label">Modifiers</div>
						<div class="discount-section" style="margin-bottom: var(--margin-sm);"></div>
						<div class="modifier-components" style="overflow-y: auto; padding: 4px 0px 1rem 0px;">
					`;
	
					frappe.call({
						method: "sultan_1975.api.api.get_item",
						args: { item_code: item.item_code },
						callback: function(modifierResponse) {
							if (modifierResponse.message.length > 0) {
								let modifierPromises = [];
								
								modifierResponse.message.forEach(function(modifier) {
									let modifierPromise = new Promise((resolve, reject) => {
										let modifierHtml = `
											<div class="modifier-item">
												<div class="expandable-header" style="margin-right: 2px; background-color: var(--control-bg); font-weight: bold; margin-bottom: 10px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; padding: 8px; border-radius: var(--border-radius-sm);">
													<span>${modifier.modifiers}</span>
													<span class="arrow-icon" style="margin-left: 10px;">▼</span> <!-- Arrow icon at far right -->
													
												</div>
												<ul class="expandable-content" style="padding: 0; margin: 0; list-style: none; display: none;"> <!-- Hidden by default -->

												
										`;
	
										// Fetch options for each modifier
										frappe.call({
											method: "sultan_1975.api.api.get_modifiers_item_option",
											args: { modifier: modifier.modifiers },
											callback: function(optionResponse) {
												var  modifiersItemsArray =[];
												if (me.current_item.modifiers_items) {
													  modifiersItemsArray = Array.isArray(me.current_item.modifiers_items)
															? [...me.current_item.modifiers_items]
															: [...Object.entries(me.current_item.modifiers_items).map(([key, value]) => ({ [key]: value }))];
														const p_index = modifiersItemsArray.findIndex(item => Object.keys(item).includes(modifier.modifiers));
													if (p_index === -1) {
														data_option_response.push({ [modifier.modifiers]: optionResponse.message });
													}
													else{
														
														data_option_response.push({ [modifier.modifiers]: [...modifiersItemsArray[p_index][modifier.modifiers].map(item => ({ ...item }))] });

														for (let i = 0; i < optionResponse.message.length; i++) {
															const items =optionResponse.message[i];
															var p_index_m =data_option_response.findIndex(item => Object.keys(item).includes(modifier.modifiers));
															if(p_index_m!==-1)
															{
																const find_index = data_option_response[p_index_m][modifier.modifiers].findIndex(item => item.item_code==items.item_code);
																if (find_index === -1) {
																	data_option_response[p_index_m][modifier.modifiers].push(items);
																}
																else
																{
																	item_is_Checked.push(items.item_code);
																}
																
															}
															
														}
													}
												} else {
													data_option_response.push({ [modifier.modifiers]: optionResponse.message });
												}
	
												var isCheckedPerant = false;
												data_option_response[data_option_response.length - 1][modifier.modifiers].forEach(function(option) {
												var	isChecked = false;
													if(item_is_Checked.length > 0 )
													{
														var c_index=item_is_Checked.findIndex(item => item === option.item_code);
														if(c_index!==-1)
														{
															isCheckedPerant=true;
														   isChecked =true;
														}
														
													}
													
													modifierHtml += `
														<li class="modifier-option-item" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; margin-right: 6px; margin-left: 8px;">
															<span style="flex: 5; text-align: left;">${option.item_name}</span>
															<span style="flex: 2; text-align: left;">${option.uom}</span>
															<span style="flex: 1; text-align: left;">${option.added_price}</span>
															<button class="decrease-btn" data-modifier="${modifier.modifiers}" data-item-code="${option.item_code}" data-item-code-modifiers="${option.item_code}-${modifier.modifiers}" data-price="${option.added_price}" style="border-radius: var(--border-radius-sm); display: flex; align-items: center; justify-content: center; padding: 0px 11px; box-shadow: var(--shadow-md); border: none; font-size: var(--text-2xl); background-color: transparent;" ${isChecked ? '' : 'disabled'}>-</button>
															<input type="number" class="qty-input" value="${option.qty}" data-modifier="${modifier.modifiers}" data-item-code="${option.item_code}" data-item-code-modifiers="${option.item_code}-${modifier.modifiers}" data-price="${option.added_price}" style="width: 50px; background-color: var(--control-bg); text-align: center; margin: 0 10px; border: none; border-radius: 5px;" ${isChecked ? '' : 'disabled'} />
															<button class="increase-btn" data-modifier="${modifier.modifiers}" data-item-code="${option.item_code}" data-item-code-modifiers="${option.item_code}-${modifier.modifiers}" data-price="${option.added_price}"  style="border-radius: var(--border-radius-sm); display: flex; align-items: center; justify-content: center; padding: 0px 11px; box-shadow: var(--shadow-md); border: none; font-size: var(--text-xl); margin-right: 20px; background-color: transparent;" ${isChecked ? '' : 'disabled'}>+</button>
															<input type="checkbox" class="select-item" data-modifier="${modifier.modifiers}" data-item-code="${option.item_code}" data-item-code-modifiers="${option.item_code}-${modifier.modifiers}" data-price="${option.added_price}" data-qty="${option.qty}" ${isChecked ? 'checked' : ''} style="margin-right: 20px;">
														</li>
													`;
												});
	
												modifierHtml += `
													</ul>
												</div>
												`;
												
												if(isCheckedPerant)
												{
													modifierHtml =modifierHtml.replace('display: none;', '');;
												}
												resolve(modifierHtml); // Resolve the promise with the modifier HTML
											}
										});
									});
	
									modifierPromises.push(modifierPromise);
								});
	
								// Wait for all modifier HTMLs to be resolved and then append them
								Promise.all(modifierPromises)
									.then(modifierHtmls => {
										htmlContent += modifierHtmls.join(''); // Combine all modifier HTMLs
										htmlContent += `</div>`; // Close the main modifier-components div
										container.append(htmlContent); // Append the final HTML content
										attachModifierHandlers(); // Attach event handlers
									});
							}
						}
					});
				}
			});
	
		// Function to attach event handlers for modifiers
		function attachModifierHandlers() {
			$('.expandable-header').click(function() {
				const section = $(this).closest('.modifier-item');
				section.toggleClass('expanded');
				const content = section.find('.expandable-content');
				content.slideToggle(); // Toggle visibility of the content
	
				// Update the arrow icon (▲ for expanded, ▼ for collapsed)
				const arrowIcon = $(this).find('.arrow-icon');
				arrowIcon.text(section.hasClass('expanded') ? '▲' : '▼');
			});
	
			// Handle checkbox click
			$('.select-item').change(function() {

				
				
				const itemCode = $(this).data('item-code');
				const modifier = $(this).data('modifier');
				const inputField = parseFloat($(`.qty-input[data-item-code="${itemCode}"]`).val());
				const inputField_element = $(`.qty-input[data-item-code="${itemCode}"]`);
				const inputField_update = $(`.qty-input[data-item-code="${itemCode}"]`);
				const increaseBtn = $(`.increase-btn[data-item-code="${itemCode}"]`);
				const decreaseBtn = $(`.decrease-btn[data-item-code="${itemCode}"]`);
				var quantity =inputField;
				const price = $(this).data('price');





				if ($(this).is(':checked')) {
					
					const doc = me.events.get_frm().doc;
					if(doc.active_coupon)
					{
					var grand_total = doc.grand_total;
					grand_total =  grand_total + doc.base_discount_amount;
					var response =  validateCoupon(grand_total ? (parseFloat(grand_total) + parseFloat(price)) : parseFloat(price) ,doc.card_value,)
						if(response.error)
						{
							frappe.msgprint(__(response.error));
							return ;
						}
					}
					// Enable input field and buttons when checked
					inputField_element.prop('disabled', false);
					increaseBtn.prop('disabled', false);
					decreaseBtn.prop('disabled', false);
					if (inputField == 0) {
						inputField_update.val(1);
					}
					updatePackedItems(itemCode, parseInt(inputField) || 1, modifier);
					const inputElement = document.querySelector('.rate-control .control-input input');
					const rate = parseFloat(parseFloat(inputElement.value.toString().replace(',', '')).toFixed(2));
					if(inputField>1)
					{
						const max =rate + (inputField * parseFloat(price));
						updateRate(max);
					}
					else
					{
						const max =rate + (1 * parseFloat(price));
						updateRate(max);
					}
					
				} else {
					// Disable input field and buttons when unchecked
					inputField_element.prop('disabled', true);
					increaseBtn.prop('disabled', true);
					decreaseBtn.prop('disabled', true);
				}



				if (!$(this).is(':checked')) {
					var max =0;
					var data_item = [];
					var data_option_doc=[];
					let modifiersItemsArray=[];
					if (me.current_item.modifiers_items) {
						modifiersItemsArray = Array.isArray(me.current_item.modifiers_items)
						? [...me.current_item.modifiers_items]
						: [...Object.entries(me.current_item.modifiers_items).map(([key, value]) => ({ [key]: value }))];
						var p_index  = modifiersItemsArray.findIndex(item => Object.keys(item).includes(modifier));
						if (p_index !== -1) {
							data_item = [...modifiersItemsArray[p_index][modifier]];
							var data=[];
							for (let i = 0; i < modifiersItemsArray[p_index][modifier].length; i++) {
								const item = modifiersItemsArray[p_index][modifier][i];
								if (item.item_code != itemCode) {
									data.push({
										modifier: modifier,
										item_name: item.item_name,
										item_code: item.item_code,
										qty: quantity,
										uom: item.uom,
										added_price: item.added_price
									});
									break; 
								}
							}
							data_option_doc.push({[modifier]:data});

						}
					}

			
					Object.entries(modifiersItemsArray).forEach(([key, value]) => {

						Object.entries(value).forEach(([key_item, value_item]) => {
							if (key_item !== modifier ) {
							
								data_option_doc.push({ [key_item] : value_item});	
							}
						});
						
						
						});


					me.events.form_updated(me.current_item, 'modifiers_items', data_option_doc, data_option_doc);
					const inputElement = document.querySelector('.rate-control .control-input input');
					const rate = parseFloat(parseFloat(inputElement.value.toString().replace(',', '')).toFixed(2));

					if(parseFloat(inputField)>1)
					{
						max =rate - (parseFloat(inputField) * parseFloat(price));
						updateRate(max);
					}
					
					else
					{
						 max =rate - (1 * parseFloat(price));
						updateRate(max);
					}
				}


				function validateCoupon(invoiceValue, cardValue) {
					const doc = me.events.get_frm().doc;
					invoiceValue = ( invoiceValue - ((doc.discount_percentage / 100) * invoiceValue));
					if(invoiceValue > cardValue && invoiceValue - cardValue >= 1)
					{
						doc.is_coupon_available=false;
						me.is_coupon_available=false;
						
					}
					else
					{
						doc.is_coupon_available=true;
						me.is_coupon_available=true;
					}
		
					if (cardValue >= invoiceValue || me.is_coupon_available) {
					  return {
						success: true
					  };
					} else {
					  return {
						error: `The invoice value ${invoiceValue} is greater than the coupon balance ${cardValue}. Please complete the order before adding any new items.`
					};
					}
				  }
			});
	
			// Handle increase button click
			$('.increase-btn').click(function() {
				const modifier = $(this).data('modifier');
				const itemCode = $(this).data('item-code');
				const price = $(this).data('price');
				const inputElement = document.querySelector('.rate-control .control-input input');
				const rate = parseFloat(parseFloat(inputElement.value.toString().replace(',', '')).toFixed(2));
				const max = rate + (1 * parseFloat(price));
				const doc = me.events.get_frm().doc;
				const inputField = $(`.qty-input[data-item-code="${itemCode}"]`);
				let quantity = parseInt(inputField.val()) || 1;
				if(doc.active_coupon)
				{
	
					var grand_total = doc.grand_total;
					grand_total =  grand_total + doc.base_discount_amount;
					var response =  validateCoupon((parseFloat(grand_total - (parseFloat(oldValue) * price)) +( parseFloat(price)* quantity )),doc.card_value,)
					if(response.error)
					{
						frappe.msgprint(__(response.error));
						inputField_update.val(oldValue);
						return ;
					}
				}
				quantity += 1;
				inputField.val(quantity);
				updatePackedItems(itemCode, quantity, modifier);
				
				updateRate(max);
			});
	
			// Handle decrease button click
			$('.decrease-btn').click(function() {
				const itemCode = $(this).data('item-code');
				const price = $(this).data('price');
				const inputField = $(`.qty-input[data-item-code="${itemCode}"]`);
				const modifier = $(this).data('modifier');
				let quantity = parseInt(inputField.val()) || 1;
				if (quantity > 1) {



					if(doc.active_coupon)
					{
						var grand_total = doc.grand_total;
						grand_total =  grand_total + doc.base_discount_amount;
						var response =  validateCoupon((parseFloat(grand_total - (parseFloat(oldValue) * price)) +( parseFloat(price)*inputField)) ,doc.card_value,)
						if(response.error)
						{
							frappe.msgprint(__(response.error));
							inputField_update.val(oldValue);
							return ;
						}
					}

					quantity -= 1;
					inputField.val(quantity);
					updatePackedItems(itemCode, quantity, modifier);
					const inputElement = document.querySelector('.rate-control .control-input input');
					const rate = parseFloat(parseFloat(inputElement.value.toString().replace(',', '')).toFixed(2));
					const max = rate - (1 * parseFloat(price));
					updateRate(max);
				}
			});
	
			let oldValue=0;
			$('.qty-input').each(function () {
				oldValue = $(this).val(); 

			   $(this).on('focus', function () {
				   oldValue = $(this).val(); 
			   });
		   });

		   
			$('.qty-input').change(function() {
				const itemCode = $(this).data('item-code');
				let quantity = parseInt($(this).val());
				const modifier = $(this).data('modifier');
				const inputField = parseFloat($(`.qty-input[data-item-code="${itemCode}"]`).val());
				const inputField_update = $(`.qty-input[data-item-code="${itemCode}"]`);
				const inputElement = document.querySelector('.rate-control .control-input input');
				const rate = parseFloat(parseFloat(inputElement.value.toString().replace(',', '')).toFixed(2));
				var max =0;
				oldValue=parseFloat(oldValue);
				const price = $(this).data('price');
				
				const doc = me.events.get_frm().doc;
				if(doc.active_coupon)
				{
					var grand_total = doc.grand_total;
					grand_total =  grand_total + doc.base_discount_amount;
					var response =  validateCoupon(quantity>oldValue?((grand_total + ((quantity-oldValue) * price))):((grand_total - (price*inputField)) + (oldValue * price)) ,doc.card_value,)
					if(response.error)
					{
						frappe.msgprint(__(response.error));
						inputField_update.val(oldValue);
						return ;
					}
				}



				if (quantity === 0 || quantity < 1) {
					
					
					updatePackedItems(itemCode, 1, modifier);

					if(inputField>=1)
					{
						var p_index = data_option_response.findIndex(item => Object.keys(item).includes(modifier));
					    var  data_item = data_option_response[p_index][modifier];
						const item = data_item.find(item => item.item_code === itemCode);

						if(item)
						{
							if(quantity>item.qty)
							{
								max =rate + ((inputField >1 ? inputField-1 : inputField) * parseFloat(price));
							}
							else if(quantity<item.qty) {
								max =rate - ((inputField >1 ? inputField-1 : inputField) * parseFloat(price));
							}
							else{
								max =rate - (item.qty * parseFloat(price));
							}
						}
						updateRate(max);
					}
					else{
						inputField_update.val(1);
					}

				} else {
					updatePackedItems(itemCode, quantity, modifier);
					if(inputField>=1)
					{
					
						if(quantity>oldValue)
						{
							max =rate + ((inputField-oldValue)  * parseFloat(price));
						}
						else if(quantity < oldValue) {

							max =rate - ((oldValue-inputField) * parseFloat(price));
						}
						else{
							max =rate;
						}
						oldValue=quantity;
						
						updateRate(max);
					}
					else
					{
						if (me.current_item.modifiers_items) {
							var  modifiersItemsArray = Array.isArray(me.current_item.modifiers_items)
							? [...me.current_item.modifiers_items]
							: [...Object.entries(me.current_item.modifiers_items).map(([key, value]) => ({ [key]: value }))];
							p_index = modifiersItemsArray.findIndex(item => Object.keys(item).includes(modifiers));
							if (p_index !== -1) {
							var data_item = [...modifiersItemsArray[p_index][modifiers]];
							 var c_index=data_item.findIndex(item => item.item_code === itemCode);
							 if(c_index!==-1)
							 {
								max =rate - (data_item[c_index].qty * parseFloat(price));
							 }
							}
						}
					}
				}
			});
		}
	function validateCoupon(invoiceValue, cardValue) {
		
			const doc = me.events.get_frm().doc;
			invoiceValue =  invoiceValue - ((doc.discount_percentage / 100) * invoiceValue);
			
			if(invoiceValue > cardValue && invoiceValue - cardValue >= 1)
			{
				doc.is_coupon_available=false;
				me.is_coupon_available=false;
				
			}
			else
			{
				doc.is_coupon_available=true;
				me.is_coupon_available=true;
			}
		
		if (cardValue >= invoiceValue || me.is_coupon_available) {
		  return {
			success: true
		  };
		} else {
		  return {
			error: `The invoice value ${invoiceValue} is greater than the coupon balance ${cardValue}. Please complete the order before adding any new items.`
		  };
		}
		}

		function updatePackedItems(itemCode, quantity, modifiers) {
			var data_item = [];
			var data_option_doc=[];
			var p_index=-1;
			let modifiersItemsArray=[];
			if (me.current_item.modifiers_items) {
				modifiersItemsArray = Array.isArray(me.current_item.modifiers_items)
				? [...me.current_item.modifiers_items]
				: [...Object.entries(me.current_item.modifiers_items).map(([key, value]) => ({ [key]: value }))];
				p_index = modifiersItemsArray.findIndex(item => Object.keys(item).includes(modifiers));
				if (p_index !== -1) {
					
					data_item = [...modifiersItemsArray[p_index][modifiers]];
					var c_index=data_item.findIndex(item => item.item_code === itemCode);
					if(c_index!==-1)
					{
						data_item[c_index].qty=quantity;
						Object.entries(modifiersItemsArray).forEach(([key, value]) => {

							Object.entries(value).forEach(([key_item, value_item]) => {
								if (key_item !== modifiers ) {
								
									data_option_doc.push({ [key_item] : value_item});	
								}
							});
							});

						data_option_doc.push({[modifiers]:data_item});
					}
					else
					{
					var p_index = data_option_response.findIndex(item => Object.keys(item).includes(modifiers));
					var  data_item = [...data_option_response[p_index][modifiers]];
					var c_index=data_item.findIndex(item => item.item_code === itemCode);
					
					var data={
						modifier: modifiers,
						item_name: data_item[c_index].item_name,
						item_code: data_item[c_index].item_code,
						qty: quantity,
						uom: data_item[c_index].uom,
						added_price: data_item[c_index].added_price
					};


					var p_index_m = modifiersItemsArray.findIndex(item => Object.keys(item).includes(modifiers));
					var data_item_update=[];
					if(p_index_m !==-1)
					{
						 data_item_update = [...modifiersItemsArray[p_index_m][modifiers]];
						 Object.entries(modifiersItemsArray).forEach(([key, value]) => {
							Object.entries(value).forEach(([key_item, value_item]) => {
							  if (key_item !== modifiers) {
								data_option_doc.push({ [key_item] : value_item});
							  }
							});
						  });
					}
					else{
						
						Object.entries(modifiersItemsArray).forEach(([key, value]) => {
							Object.entries(value).forEach(([key_item, value_item]) => {
							  if (key_item !== modifiers) {
								data_option_doc.push({ [key_item] : value_item});
							  }
							});
						
						});
						
					}
		
					data_item_update.push(data)
					
					data_option_doc.push({[modifiers]:data_item_update});
							
					}
		
				}

				else{
					var p_index = data_option_response.findIndex(item => Object.keys(item).includes(modifiers));
					var  data_item = [...data_option_response[p_index][modifiers]];
					var c_index=data_item.findIndex(item => item.item_code === itemCode);
					var data={
						modifier: modifiers,
						item_name: data_item[c_index].item_name,
						item_code: data_item[c_index].item_code,
						qty: quantity,
						uom: data_item[c_index].uom,
						added_price: data_item[c_index].added_price
					};
					var p_index_m = modifiersItemsArray.findIndex(item => Object.keys(item).includes(modifiers));
					var data_item_update=[];
					if(p_index_m !==-1)
					{
						 data_item_update = [...modifiersItemsArray[p_index_m][modifiers]];
						  Object.entries(modifiersItemsArray).forEach(([key, value]) => {
							Object.entries(value).forEach(([key_item, value_item]) => {
							  if (key_item !== modifiers) {
								data_option_doc.push({ [key_item] : value_item});
							  }
							});
						  });
					}
					else{
					  Object.entries(modifiersItemsArray).forEach(([key, value]) => {
							Object.entries(value).forEach(([key_item, value_item]) => {
							  if (key_item !== modifiers) {
								data_option_doc.push({ [key_item] : value_item});
							  }
							});
						  });
					}
					data_item_update.push(data)
					data_option_doc.push({[modifiers]:data_item_update});
				}
			}
				
				

				else {
					var p_index = data_option_response.findIndex(item => Object.keys(item).includes(modifiers));
					var  data_item = [...data_option_response[p_index][modifiers]];
					var c_index=data_item.findIndex(item => item.item_code === itemCode);
					var data={
						modifier: modifiers,
						item_name: data_item[c_index].item_name,
						item_code: data_item[c_index].item_code,
						qty: quantity,
						uom: data_item[c_index].uom,
						added_price: data_item[c_index].added_price
					};
					data_option_doc.push({[modifiers]:[data]});
				}
		
				me.events.form_updated(me.current_item, 'modifiers_items', data_option_doc, data_option_doc);	
		}
	
		function updateRate(max) {
			me.events.form_updated(me.current_item, 'rate', max).then(() => {
				const item_row = frappe.get_doc(me.doctype, me.current_item.name);
				const doc = me.events.get_frm().doc;
				me.$item_price.html(format_currency(item_row.rate, doc.currency));
				me.render_discount_dom(item_row);
			});
		}
	}
	

	get_form_fields(item) {

		const fields = ['qty', 'uom', 'rate', 'conversion_factor', 'discount_percentage', 'warehouse', 'actual_qty', 'price_list_rate'];
		if (item.has_serial_no) fields.push('serial_no');
		if (item.has_batch_no) fields.push('batch_no');
		return fields;
	}

	make_auto_serial_selection_btn(item) {
		if (item.has_serial_no || item.has_batch_no) {
			const label = item.has_serial_no ? __('Select Serial No') : __('Select Batch No');
			this.$form_container.append(
				`<div class="btn btn-sm btn-secondary auto-fetch-btn">${label}</div>`
			);
			this.$form_container.find('.serial_no-control').find('textarea').css('height', '6rem');
		}
	}

	bind_custom_control_change_event() {
		const me = this;
		if (this.rate_control) {
			this.rate_control.df.onchange = function() {

			
				
				const doc = me.events.get_frm().doc;
				if(doc.active_coupon)
				{
					
					var response =  validateCoupon(doc.grand_total ? ((parseFloat(doc.grand_total) - me.current_item.base_net_amount) + parseFloat(me.current_item.qty * this.value)) : parseFloat(me.current_item.base_price_list_rate) , doc.card_value, me , { fieldname :'rate' , value : me.current_item.rate})
					if(response.error)
					{
						frappe.msgprint(__(response.error));
						return ;
					}
				}


				if (this.value || flt(this.value) === 0) {
					me.events.form_updated(me.current_item, 'rate', this.value).then(() => {
						const item_row = frappe.get_doc(me.doctype, me.name);
						const doc = me.events.get_frm().doc;
						me.$item_price.html(format_currency(item_row.rate, doc.currency));
						me.render_discount_dom(item_row);
					});
				}

				function validateCoupon(invoiceValue, cardValue ,me , { fieldname=null , value=null}) {
	
					const doc = me.events.get_frm().doc;
					invoiceValue = ( invoiceValue - ((doc.discount_percentage / 100) * invoiceValue));
					if(invoiceValue > cardValue && invoiceValue - cardValue >= 1)
					{
						doc.is_coupon_available=false;
						me.is_coupon_available=false;
						
					}
					else
					{
						doc.is_coupon_available=true;
						me.is_coupon_available=true;
					}
		
					if (cardValue >= invoiceValue || me.is_coupon_available) {
					  return {
						success: true
					  };
					} else {
						if(fieldname)
						{
							me[`${fieldname}_control`].set_value(value);
						}
					  return {
						error: `The invoice value ${invoiceValue} is greater than the coupon balance ${cardValue}. Please complete the order before adding any new items.`
					};
					}
				  }
			};
			this.rate_control.df.read_only = !this.allow_rate_change;
			this.rate_control.refresh();
		}

		if (this.discount_percentage_control && !this.allow_discount_change) {
			this.discount_percentage_control.df.read_only = 1;
			this.discount_percentage_control.refresh();
		}

		if (this.warehouse_control) {
			this.warehouse_control.df.reqd = 1;
			this.warehouse_control.df.onchange = function() {
				if (this.value) {
					me.events.form_updated(me.current_item, 'warehouse', this.value).then(() => {
						me.item_stock_map = me.events.get_item_stock_map();
						const available_qty = me.item_stock_map[me.item_row.item_code][this.value][0];
						const is_stock_item = Boolean(me.item_stock_map[me.item_row.item_code][this.value][1]);
						if (available_qty === undefined) {
							me.events.get_available_stock(me.item_row.item_code, this.value).then(() => {
								// item stock map is updated now reset warehouse
								me.warehouse_control.set_value(this.value);
							})
						} else if (available_qty === 0 && is_stock_item) {
							me.warehouse_control.set_value('');
							const bold_item_code = me.item_row.item_code.bold();
							const bold_warehouse = this.value.bold();
							frappe.throw(
								__('Item Code: {0} is not available under warehouse {1}.', [bold_item_code, bold_warehouse])
							);
						}
						me.actual_qty_control.set_value(available_qty);
					});
				}
			}
			this.warehouse_control.df.get_query = () => {
				return {
					filters: { company: this.events.get_frm().doc.company }
				}
			};
			this.warehouse_control.refresh();
		}

		if (this.serial_no_control) {
			this.serial_no_control.df.reqd = 1;
			this.serial_no_control.df.onchange = async function() {
				!me.current_item.batch_no && await me.auto_update_batch_no();
				me.events.form_updated(me.current_item, 'serial_no', this.value);
			}
			this.serial_no_control.refresh();
		}

		if (this.batch_no_control) {
			this.batch_no_control.df.reqd = 1;
			this.batch_no_control.df.get_query = () => {
				return {
					query: 'erpnext.controllers.queries.get_batch_no',
					filters: {
						item_code: me.item_row.item_code,
						warehouse: me.item_row.warehouse,
						posting_date: me.events.get_frm().doc.posting_date
					}
				}
			};
			this.batch_no_control.refresh();
		}

		if (this.uom_control) {
			this.uom_control.df.onchange = function() {
				me.events.form_updated(me.current_item, 'uom', this.value);

				const item_row = frappe.get_doc(me.doctype, me.name);
				me.conversion_factor_control.df.read_only = (item_row.stock_uom == this.value);
				me.conversion_factor_control.refresh();
			}
		}

		frappe.model.on("POS Invoice Item", "*", (fieldname, value, item_row) => {
			const field_control = this[`${fieldname}_control`];
			const item_row_is_being_edited = this.compare_with_current_item(item_row);
			if (
				item_row_is_being_edited &&
				field_control &&
				field_control.get_value() !== value &&
				value == item_row[fieldname]
			) {
				field_control.set_value(value);
				cur_pos.update_cart_html(item_row);
			}
		});
	}

	async auto_update_batch_no() {
		if (this.serial_no_control && this.batch_no_control) {
			const selected_serial_nos = this.serial_no_control.get_value().split(`\n`).filter(s => s);
			if (!selected_serial_nos.length) return;

			// find batch nos of the selected serial no
			const serials_with_batch_no = await frappe.db.get_list("Serial No", {
				filters: { 'name': ["in", selected_serial_nos]},
				fields: ["batch_no", "name"]
			});
			const batch_serial_map = serials_with_batch_no.reduce((acc, r) => {
				if (!acc[r.batch_no]) {
					acc[r.batch_no] = [];
				}
				acc[r.batch_no] = [...acc[r.batch_no], r.name];
				return acc;
			}, {});
			// set current item's batch no and serial no
			const batch_no = Object.keys(batch_serial_map)[0];
			const batch_serial_nos = batch_serial_map[batch_no].join(`\n`);
			// eg. 10 selected serial no. -> 5 belongs to first batch other 5 belongs to second batch
			const serial_nos_belongs_to_other_batch = selected_serial_nos.length !== batch_serial_map[batch_no].length;

			const current_batch_no = this.batch_no_control.get_value();
			current_batch_no != batch_no && await this.batch_no_control.set_value(batch_no);

			if (serial_nos_belongs_to_other_batch) {
				this.serial_no_control.set_value(batch_serial_nos);
				this.qty_control.set_value(batch_serial_map[batch_no].length);

				delete batch_serial_map[batch_no];
				this.events.clone_new_batch_item_in_frm(batch_serial_map, this.current_item);
			}
		}
	}

	bind_events() {
		this.bind_auto_serial_fetch_event();
		this.bind_fields_to_numpad_fields();

		this.$component.on('click', '.close-btn', () => {
			this.events.close_item_details();
		});
	}

	attach_shortcuts() {
		this.wrapper.find('.close-btn').attr("title", "Esc");
		frappe.ui.keys.on("escape", () => {
			const item_details_visible = this.$component.is(":visible");
			if (item_details_visible) {
				this.events.close_item_details();
			}
		});
	}

	bind_fields_to_numpad_fields() {
		const me = this;
		this.$form_container.on('click', '.input-with-feedback', function() {
			const fieldname = $(this).attr('data-fieldname');
			if (this.last_field_focused != fieldname) {
				me.events.item_field_focused(fieldname);
				this.last_field_focused = fieldname;
			}
		});
	}

	bind_auto_serial_fetch_event() {
		this.$form_container.on('click', '.auto-fetch-btn', () => {
			frappe.require("assets/erpnext/js/utils/serial_no_batch_selector.js", () => {
				let frm = this.events.get_frm();
				let item_row = this.item_row;
				item_row.type_of_transaction = "Outward";

				new erpnext.SerialBatchPackageSelector(frm, item_row, (r) => {
					if (r) {
						frappe.model.set_value(item_row.doctype, item_row.name, {
							"serial_and_batch_bundle": r.name,
							"qty": Math.abs(r.total_qty)
						});
					}
				});
			});
		})
	}

	toggle_component(show) {
		show ? this.$component.css('display', 'flex') : this.$component.css('display', 'none');
	}
}
