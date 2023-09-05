# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import json

import frappe
from frappe.utils.nestedset import get_root_of

from erpnext.accounts.doctype.pos_profile.pos_profile import get_item_groups
from erpnext.accounts.doctype.pos_invoice.pos_invoice import get_stock_availability
from erpnext.stock.get_item_details import get_item_price
from datetime import date


def search_by_term(search_term, warehouse, price_list):
	result = search_for_serial_or_batch_or_barcode_number(search_term) or {}

	item_code = result.get("item_code") or search_term
	serial_no = result.get("serial_no") or ""
	batch_no = result.get("batch_no") or ""
	barcode = result.get("barcode") or ""

	if result:
		item_info = frappe.db.get_value("Item", item_code,
			["name as item_code", "item_name", "description", "stock_uom", "image as item_image", "is_stock_item"],
			as_dict=1)
	
		item_stock_qty = get_stock_availability(item_code, warehouse , batch_no)

		args = {
				'item_code' : item_code,
				'price_list': price_list,
				'uom' : item_info['stock_uom'],
				'posting_date' : date.today(),
				'batch_no' : batch_no
				}		
		price_info = get_item_price(args , item_code)
		if price_info:
			price_list_rate , currency = price_info[0][1] , price_info[0][3]			
		else:	
			price_list_rate , currency = [None, None]
		item_info.update({
			'serial_no': serial_no,
			'batch_no': batch_no,
			'barcode': barcode,
			'price_list_rate': price_list_rate,
			'currency': currency,
			'actual_qty': item_stock_qty
		})

		return {'items': [item_info]}

@frappe.whitelist()
def get_items(start, page_length, price_list, item_group, pos_profile, search_term=""):
	warehouse, hide_unavailable_items = frappe.db.get_value(
		'POS Profile', pos_profile, ['warehouse', 'hide_unavailable_items'])

	result = []

	if search_term:
		result = search_by_term(search_term, warehouse, price_list) or []
		if result:
			return result

	if not frappe.db.exists('Item Group', item_group):
		item_group = get_root_of('Item Group')

	condition = get_conditions(search_term)
	condition += get_item_group_condition(pos_profile)

	lft, rgt = frappe.db.get_value('Item Group', item_group, ['lft', 'rgt'])

	items_data = frappe.db.sql(f"""
		SELECT DISTINCT
			item.name AS item_code,
			item.item_name,
			item.description,
			item.stock_uom AS stock_uom,
			item.image AS item_image,
			item.is_stock_item,
			`tabBatch`.name AS batch_no
		FROM
			`tabItem` item 
				INNER JOIN `tabBatch` ON tabBatch.item =  item.item_code
				AND tabBatch.disabled = 0 AND tabBatch.batch_qty > 0
				AND (tabBatch.expiry_date > CURRENT_TIMESTAMP OR tabBatch.expiry_date = '' OR tabBatch.expiry_date is null)
				INNER JOIN `tabStock Ledger Entry` AS tabStockLedgerEntry ON tabStockLedgerEntry.item_code = item.item_code
				AND tabStockLedgerEntry.warehouse = '{warehouse}'  AND tabStockLedgerEntry.batch_no = tabBatch.name AND tabStockLedgerEntry.actual_qty > 0
			
		WHERE
			item.disabled = 0
			AND item.has_variants = 0
			AND item.is_sales_item = 1
			AND item.is_fixed_asset = 0
			AND item.item_group in (SELECT name FROM `tabItem Group` WHERE lft >= {lft} AND rgt <= {rgt})
		
		ORDER BY
			item.name asc
		LIMIT
			{start}, {page_length}"""
		.format(
			start=start,
			page_length=page_length,
			lft=lft,
			rgt=rgt,
			condition=condition		
		), as_dict=1)

	if items_data:
		items_data = filter_service_items(items_data)	

		for item in items_data:	
			item_code = item.item_code	
			batch_no = item.batch_no
			stock_uom = item.stock_uom
			args = {
				'item_code' : item_code,
				'price_list': price_list,
				'uom' : stock_uom,
				'posting_date' : date.today(),
				'batch_no' : batch_no
				}		
			price_info = get_item_price(args , item_code)
			if price_info:
				price_list_rate , currency = price_info[0][1] , price_info[0][3]			
			else:	
				price_list_rate , currency = [None, None]

			item_stock_qty = get_stock_availability(item_code, warehouse , batch_no)	

			if  hide_unavailable_items:
				if item_stock_qty > 0:			
					row = {}
					row.update(item)
					row.update({
						'price_list_rate':price_list_rate ,
						'currency': currency,
						'actual_qty': item_stock_qty,
					})
					result.append(row)
			else:
				row = {}
				row.update(item)
				row.update({
					'price_list_rate': price_list_rate,
					'currency': currency,
					'actual_qty': item_stock_qty,
				})
				result.append(row)
	
	return {'items': result}

@frappe.whitelist()
def search_for_serial_or_batch_or_barcode_number(search_value):
	# search barcode no
	barcode_data = frappe.db.get_value('Item Barcode', {'barcode': search_value}, ['barcode', 'batch_no', 'parent as item_code'], as_dict=True)
	if barcode_data:
		# custom update
		from datetime import date
		barcode_data_nobatch = frappe.db.get_value('Item Barcode', {'barcode': search_value}, ['barcode', 'parent as item_code'], as_dict=True)
		batch_no_validate = frappe.db.get_value('Batch', barcode_data.batch_no, ['name as batch_no', 'item as item_code','batch_qty','disabled','expiry_date'], as_dict=True)
		if batch_no_validate:
			if batch_no_validate.batch_qty==0 or batch_no_validate.disabled==1 or not batch_no_validate.expiry_date or batch_no_validate.expiry_date  < date.today():
				return barcode_data_nobatch
			else:
				return barcode_data		
		else:
			return barcode_data

	# search serial no
	serial_no_data = frappe.db.get_value('Serial No', search_value, ['name as serial_no', 'item_code'], as_dict=True)
	if serial_no_data:
		return serial_no_data

	# search batch no
	batch_no_data = frappe.db.get_value('Batch', search_value, ['name as batch_no', 'item as item_code'], as_dict=True)
	if batch_no_data:
		return batch_no_data

	return {}

def filter_service_items(items):
	for item in items:
		if not item['is_stock_item']:
			if not frappe.db.exists('Product Bundle', item['item_code']):
				items.remove(item)

	return items

def get_conditions(search_term):
	condition = "("
	condition += """item.name like {search_term}
		or item.item_name like {search_term}""".format(search_term=frappe.db.escape('%' + search_term + '%'))
	condition += add_search_fields_condition(search_term)
	condition += ")"

	return condition

def add_search_fields_condition(search_term):
	condition = ''
	search_fields = frappe.get_all('POS Search Fields', fields = ['fieldname'])
	if search_fields:
		for field in search_fields:
			condition += " or item.`{0}` like {1}".format(field['fieldname'], frappe.db.escape('%' + search_term + '%'))
	return condition

def get_item_group_condition(pos_profile):
	cond = "and 1=1"
	item_groups = get_item_groups(pos_profile)
	if item_groups:
		cond = "and item.item_group in (%s)"%(', '.join(['%s']*len(item_groups)))

	return cond % tuple(item_groups)

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def item_group_query(doctype, txt, searchfield, start, page_len, filters):
	item_groups = []
	cond = "1=1"
	pos_profile= filters.get('pos_profile')

	if pos_profile:
		item_groups = get_item_groups(pos_profile)

		if item_groups:
			cond = "name in (%s)"%(', '.join(['%s']*len(item_groups)))
			cond = cond % tuple(item_groups)

	return frappe.db.sql(""" select distinct name from `tabItem Group`
			where {condition} and (name like %(txt)s) limit {start}, {page_len}"""
		.format(condition = cond, start=start, page_len= page_len),
			{'txt': '%%%s%%' % txt})

@frappe.whitelist()
def check_opening_entry(user):
	open_vouchers = frappe.db.get_all("POS Opening Entry",
		filters = {
			"user": user,
			"pos_closing_entry": ["in", ["", None]],
			"docstatus": 1
		},
		fields = ["name", "company", "pos_profile", "period_start_date"],
		order_by = "period_start_date desc"
	)

	return open_vouchers

@frappe.whitelist()
def create_opening_voucher(pos_profile, company, balance_details):
	balance_details = json.loads(balance_details)

	new_pos_opening = frappe.get_doc({
		'doctype': 'POS Opening Entry',
		"period_start_date": frappe.utils.get_datetime(),
		"posting_date": frappe.utils.getdate(),
		"user": frappe.session.user,
		"pos_profile": pos_profile,
		"company": company,
	})
	new_pos_opening.set("balance_details", balance_details)
	new_pos_opening.submit()

	return new_pos_opening.as_dict()

@frappe.whitelist()
def get_past_order_list(search_term, status, limit=20):
	fields = ['name', 'grand_total', 'currency', 'customer', 'posting_time', 'posting_date']
	invoice_list = []

	if search_term and status:
		invoices_by_customer = frappe.db.get_all('POS Invoice', filters={
			'customer': ['like', '%{}%'.format(search_term)],
			'status': status
		}, fields=fields)
		invoices_by_name = frappe.db.get_all('POS Invoice', filters={
			'name': ['like', '%{}%'.format(search_term)],
			'status': status
		}, fields=fields)

		invoice_list = invoices_by_customer + invoices_by_name
	elif status:
		invoice_list = frappe.db.get_all('POS Invoice', filters={
			'status': status
		}, fields=fields)

	return invoice_list

@frappe.whitelist()
def set_customer_info(fieldname, customer, value=""):
	if fieldname == 'loyalty_program':
		frappe.db.set_value('Customer', customer, 'loyalty_program', value)

	contact = frappe.get_cached_value('Customer', customer, 'customer_primary_contact')
	if not contact:
		contact = frappe.db.sql("""
			SELECT parent FROM `tabDynamic Link`
			WHERE
				parenttype = 'Contact' AND
				parentfield = 'links' AND
				link_doctype = 'Customer' AND
				link_name = %s
			""", (customer), as_dict=1)
		contact = contact[0].get('parent') if contact else None

	if not contact:
		new_contact = frappe.new_doc('Contact')
		new_contact.is_primary_contact = 1
		new_contact.first_name = customer
		new_contact.set('links', [{'link_doctype': 'Customer', 'link_name': customer}])
		new_contact.save()
		contact = new_contact.name
		frappe.db.set_value('Customer', customer, 'customer_primary_contact', contact)

	contact_doc = frappe.get_doc('Contact', contact)
	if fieldname == 'email_id':
		contact_doc.set('email_ids', [{ 'email_id': value, 'is_primary': 1}])
		frappe.db.set_value('Customer', customer, 'email_id', value)
	elif fieldname == 'mobile_no':
		contact_doc.set('phone_nos', [{ 'phone': value, 'is_primary_mobile_no': 1}])
		frappe.db.set_value('Customer', customer, 'mobile_no', value)
	contact_doc.save()
