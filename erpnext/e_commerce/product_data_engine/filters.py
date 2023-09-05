# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
import frappe
from frappe.utils import floor


class ProductFiltersBuilder:
	def __init__(self, item_group=None, filters=None): ###Custom Update
		if not item_group:
			self.doc = frappe.get_doc("E Commerce Settings")
		else:
			self.doc = frappe.get_doc("Item Group", item_group)

		self.item_group = item_group
		### Custom Update
		if filters:
			self.filters = filters
		else :
			self.filters = None
		### End Custom Update

	def get_field_filters(self):
		if not self.item_group and not self.doc.enable_field_filters:
			return

		fields, filter_data = [], []
		filter_fields = [row.fieldname for row in self.doc.filter_fields] # fields in settings

		# filter valid field filters i.e. those that exist in Item
		item_meta = frappe.get_meta('Item', cached=True)
		fields = [item_meta.get_field(field) for field in filter_fields if item_meta.has_field(field)]
		### Custom update
		filters = self.filters
		for df in fields:
			multi_select_filters = ''
			child_doctype = ''
			item_filters, item_or_filters = {}, []
			link_doctype_values = self.get_filtered_link_doctype_records(df)

			if df.fieldtype == "Link":
				if self.item_group:
					item_or_filters.extend([
						["item_group", "=", self.item_group],
						["Website Item Group", "item_group", "=", self.item_group] # consider website item groups
					])
				## Custom Update
				strQuery = "SELECT " + df.fieldname
				strFrom = """ FROM `tabWebsite Item` AS w """
				strWhere = "WHERE published = 1 "
				if filters:
					for filter_name in filters.keys():
						for f in fields:
							if f.fieldname == filter_name:
								typefield = f.fieldtype
								if typefield == 'Table MultiSelect':
									child_doctype = f.options
									child_meta = frappe.get_meta(child_doctype, cached=True)
									doc_fields = child_meta.get("fields")
									if doc_fields:
										multi_select_filters= doc_fields[0].fieldname
								break
						if filter_name != df.fieldname and (typefield == "Link"):
							strWhere += "AND "+ filter_name + "=" + "'"+ filters[filter_name][0] + "' "
							for i  in range(1, len(filters[filter_name])):
								strWhere += "OR " + filter_name + "=" + "'" + filters[filter_name][i] + "' "
						else: 
							if (typefield == 'Table MultiSelect'):
								strFrom += " INNER JOIN `tab"+ child_doctype +"` ON w.item_code = `tab"+ child_doctype +"`.parent  "
								strWhere +=" AND `tab"+ child_doctype +"`." +multi_select_filters+" IN ("+ "'" + filters[filter_name][0] + "'" +") "
								for i  in range(2, len(filters[filter_name])):
									strWhere += "OR `tab"+ child_doctype +"`." +multi_select_filters+" IN ("+ "'" + filters[filter_name][i] + "'" +") "
				strQuery += strFrom + strWhere
				res = frappe.db.sql(strQuery, as_list = 1)
				res = sum(res, [])
				## End Custom Update

				# Get link field values attached to published items
				### Custom Comments ###
				# item_filters['published'] = 1  ###Custom Update
				# item_values = frappe.get_all(
				# 	"Website Item",   ###Custom Update
				# 	fields=[df.fieldname],
				# 	filters=item_filters,
				# 	or_filters=item_or_filters,
				# 	distinct="True",
				# 	pluck=df.fieldname
				# )
				values = list(set(res) & link_doctype_values) # intersection of both
			else:
				### Custom Update
				if df.fieldtype == 'Table MultiSelect':
					child_doctype = df.options
					child_meta = frappe.get_meta(child_doctype, cached=True)
					doc_fields = child_meta.get("fields")
					if doc_fields:
						multi_select_filters= doc_fields[0].fieldname
				if filters:
					strQuery = "SELECT `tab"+ child_doctype +"`." + multi_select_filters
					strFrom = " FROM `tabWebsite Item` AS w INNER JOIN `tab"+ child_doctype +"` ON w.item_code = `tab"+ child_doctype +"`.parent "
					strWhere = "WHERE published = 1 "
					for filter_name in filters.keys():
						for f in fields:
							if f.fieldname == filter_name:
								typefield = f.fieldtype
								if typefield == 'Table MultiSelect':
									filter_child_doctype = f.options
									child_meta = frappe.get_meta(filter_child_doctype, cached=True)
									doc_fields = child_meta.get("fields")
									if doc_fields:
										field_multi_select_filters= doc_fields[0].fieldname
								break
						if filter_name != df.fieldname and (typefield == "Link"):
							strWhere += "AND w."+ filter_name + "=" + "'"+ filters[filter_name][0] + "' "
							for i  in range(2, len(filters[filter_name])):
								strWhere += "OR w." + filter_name + "=" + "'" + filters[filter_name][i] + "' "
						# if filter_name != df.fieldname and (typefield == "Table MultiSelect"):
						# 	strFrom += " INNER JOIN `tab"+ filter_child_doctype +"` ON w.item_code = `tab"+ filter_child_doctype +"`.parent  "
						# 	strWhere +=" AND `tab"+ filter_child_doctype +"`." +field_multi_select_filters+" IN ("+ "'" + filters[filter_name][0] + "'" +") "
						# 	for i  in range(2, len(filters[filter_name])):
						# 		strWhere += "OR `tab"+ filter_child_doctype +"`." +field_multi_select_filters+" IN ("+ "'" + filters[filter_name][i] + "'" +") "
					strQuery += strFrom + strWhere
					res = frappe.db.sql(strQuery, as_list = 1)
					res = sum(res, [])
					values = list(set(res) & link_doctype_values)
				else:
					# table multiselect
					values = list(link_doctype_values)
				### End Custom Update

			# Remove None
			if None in values:
				values.remove(None)

			if values:
				filter_data.append([df, values])

		return filter_data

	def get_filtered_link_doctype_records(self, field):
		"""
			Get valid link doctype records depending on filters.
			Apply enable/disable/show_in_website filter.
			Returns:
				set: A set containing valid record names
		"""
		link_doctype = field.get_link_doctype()
		meta = frappe.get_meta(link_doctype, cached=True) if link_doctype else None
		if meta:
			filters = self.get_link_doctype_filters(meta)
			link_doctype_values = set(d.name for d in frappe.get_all(link_doctype, filters))

		return link_doctype_values if meta else set()

	def get_link_doctype_filters(self, meta):
		"Filters for Link Doctype eg. 'show_in_website'."
		filters = {}
		if not meta:
			return filters

		if meta.has_field('enabled'):
			filters['enabled'] = 1
		if meta.has_field('disabled'):
			filters['disabled'] = 0
		if meta.has_field('show_in_website'):
			filters['show_in_website'] = 1

		return filters

	def get_attribute_filters(self):
		if not self.item_group and not self.doc.enable_attribute_filters:
			return

		attributes = [row.attribute for row in self.doc.filter_attributes]

		if not attributes:
			return []

		result = frappe.db.sql(
			"""
			select
				distinct attribute, attribute_value
			from
				`tabItem Variant Attribute`
			where
				attribute in %(attributes)s
				and attribute_value is not null
		""",
			{"attributes": attributes},
			as_dict=1,
		)

		attribute_value_map = {}
		for d in result:
			attribute_value_map.setdefault(d.attribute, []).append(d.attribute_value)

		out = []
		for name, values in attribute_value_map.items():
			out.append(frappe._dict(name=name, item_attribute_values=values))
		return out

	def get_discount_filters(self, discounts):
		discount_filters = []

		# [25.89, 60.5] min max
		min_discount, max_discount = discounts[0], discounts[1]
		# [25, 60] rounded min max
		min_range_absolute, max_range_absolute = floor(min_discount), floor(max_discount)

		min_range = int(min_discount - (min_range_absolute % 10)) # 20
		max_range = int(max_discount - (max_range_absolute % 10)) # 60

		min_range = (min_range + 10) if min_range != min_range_absolute else min_range # 30 (upper limit of 25.89 in range of 10)
		max_range = (max_range + 10) if max_range != max_range_absolute else max_range # 60

		for discount in range(min_range, (max_range + 1), 10):
			label = f"{discount}% and below"
			discount_filters.append([discount, label])

		return discount_filters
