# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils import cint, cstr
from redisearch import AutoCompleter, Client, Query

from erpnext.e_commerce.redisearch_utils import (
	WEBSITE_ITEM_CATEGORY_AUTOCOMPLETE,
	WEBSITE_ITEM_INDEX,
	WEBSITE_ITEM_NAME_AUTOCOMPLETE,
	is_search_module_loaded,
	make_key,
)
from erpnext.e_commerce.shopping_cart.product_info import set_product_info_for_website
from erpnext.setup.doctype.item_group.item_group import get_item_for_list_in_html

no_cache = 1

def get_context(context):
	context.show_search = True

@frappe.whitelist(allow_guest=True)
def get_product_list(search=None, start=0, limit=12):
	data = get_product_data(search, start, limit)

	for item in data:
		set_product_info_for_website(item)

	return [get_item_for_list_in_html(r) for r in data]

def get_product_data(search=None ,start=0, limit=12, page=""): ##custom update
	# limit = 12 because we show 12 items in the grid view
	# base query
	## custom update
	query = """
		SELECT DISTINCT
			tabWebsiteItem.web_item_name, tabWebsiteItem.item_name, tabWebsiteItem.item_code, tabWebsiteItem.brand, tabWebsiteItem.route,
			tabWebsiteItem.website_image, tabWebsiteItem.thumbnail, tabWebsiteItem.item_group,
			tabWebsiteItem.description, tabWebsiteItem.web_long_description as website_description,
			tabWebsiteItem.website_warehouse, tabWebsiteItem.ranking , tabBatch.name AS batch_no,
			tabBatch.ranking AS batch_ranking , tabBatch.expiry_date AS expiry_date
		
		"""
	strFrom = """
		FROM `tabWebsite Item` AS tabWebsiteItem				
				INNER  JOIN `tabBatch` ON tabBatch.item =  tabWebsiteItem.item_name AND tabBatch.disabled = 0 AND (expiry_date > CURRENT_TIMESTAMP OR expiry_date = '' OR expiry_date is null)
				INNER JOIN `tabStock Ledger Entry` AS tabStockLedgerEntry ON tabStockLedgerEntry.item_code = tabWebsiteItem.item_code
				AND tabStockLedgerEntry.warehouse = 'Kensington Main Store - M'  AND tabStockLedgerEntry.batch_no = tabBatch.name
				AND tabStockLedgerEntry.actual_qty > 0 
	"""
	strWhere = ' WHERE published = 1 ' 
	# search term condition
	if search:
		if (page=='best_value'):
			strFrom += ' INNER JOIN `tabItem Best Value` AS  tabItemBestValue  ON tabItemBestValue.item_code = tabWebsiteItem.item_code '
			strWhere += ' AND tabItemBestValue.batch_id = tabBatch.name '
		else: 
			if (page =='pre_order'):
				strFrom += ' INNER JOIN `tabItem PreOrder` AS  tabItemPreOrder  ON tabItemPreOrder.item_code = tabWebsiteItem.item_code '
				strWhere += ' AND tabItemPreOrder.batch_id = tabBatch.name '
		strWhere += """ and (tabWebsiteItem.item_name like %(search)s
				or tabWebsiteItem.web_item_name like %(search)s
				or tabWebsiteItem.brand like %(search)s
				or tabWebsiteItem._user_tags like %(search)s
				or tabWebsiteItem.web_long_description like %(search)s)"""
		search = "%" + cstr(search) + "%"

	# order by
	query += strFrom + strWhere+ """ ORDER BY batch_ranking desc , tabWebsiteItem.modified desc limit %s, %s""" % (cint(start), cint(limit))

	return frappe.db.sql(query, {
		"search": search
	}, as_dict=1)

@frappe.whitelist(allow_guest=True)
def search(query, page): ##custom update
	product_results = product_search(query, page = page) ##custom update
	category_results = get_category_suggestions(query)

	return {
		"product_results": product_results.get("results") or [],
		"category_results": category_results.get("results") or []
	}

@frappe.whitelist(allow_guest=True)
def product_search(query, limit=10, fuzzy_search=True, page = ""): ##custom update
	search_results = {"from_redisearch": True, "results": []}

	if not is_search_module_loaded():
		# Redisearch module not loaded
		search_results["from_redisearch"] = False
		search_results["results"] = get_product_data(query, 0, limit, page) ##custom update
		return search_results

	if not query:
		return search_results

	red = frappe.cache()
	query = clean_up_query(query)

	ac = AutoCompleter(make_key(WEBSITE_ITEM_NAME_AUTOCOMPLETE), conn=red)
	client = Client(make_key(WEBSITE_ITEM_INDEX), conn=red)
	suggestions = ac.get_suggestions(
		query,
		num=limit,
		fuzzy= fuzzy_search and len(query) > 3 # Fuzzy on length < 3 can be real slow
	)

	# Build a query
	query_string = query

	for s in suggestions:
		query_string += f"|('{clean_up_query(s.string)}')"

	q = Query(query_string)

	results = client.search(q)
	search_results['results'] = list(map(convert_to_dict, results.docs))
	search_results['results'] = sorted(search_results['results'], key=lambda k: frappe.utils.cint(k['ranking']), reverse=True)

	return search_results

def clean_up_query(query):
	return ''.join(c for c in query if c.isalnum() or c.isspace())

def convert_to_dict(redis_search_doc):
	return redis_search_doc.__dict__

@frappe.whitelist(allow_guest=True)
def get_category_suggestions(query):
	search_results = {"results": []}

	if not is_search_module_loaded():
		# Redisearch module not loaded, query db
		categories = frappe.db.get_all(
			"Item Group",
			filters={
				"name": ["like", "%{0}%".format(query)],
				"show_in_website": 1
			},
			fields=["name", "route"]
		)
		search_results['results'] = categories
		return search_results

	if not query:
		return search_results

	ac = AutoCompleter(make_key(WEBSITE_ITEM_CATEGORY_AUTOCOMPLETE), conn=frappe.cache())
	suggestions = ac.get_suggestions(query, num=10)

	search_results['results'] = [s.string for s in suggestions]

	return search_results
