# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document
from frappe.website.utils import delete_page_cache


class Homepage(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from webshop.webshop.doctype.homepage_featured_product.homepage_featured_product import HomepageFeaturedProduct

		company: DF.Link
		description: DF.Text
		hero_image: DF.AttachImage | None
		hero_section: DF.Link | None
		hero_section_based_on: DF.Literal["Default", "Slideshow", "Homepage Section"]
		products: DF.Table[HomepageFeaturedProduct]
		products_url: DF.Data | None
		slideshow: DF.Link | None
		tag_line: DF.Data
		title: DF.Data | None
	# end: auto-generated types

	def validate(self):
		if not self.description:
			self.description = frappe._("This is an example website auto-generated from ERPNext")
		delete_page_cache("home")
