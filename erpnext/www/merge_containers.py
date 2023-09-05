import frappe
from frappe import _
from kensingtonbn.kensingtonbn.doctype.container_reconciliation.container_reconciliation import get_items


@frappe.whitelist(allow_guest = True)
def merge_containers(container1 , container2): 
    doc1 = frappe.get_doc('Container Reconciliation' , container1)
    doc2 = frappe.get_doc('Container Reconciliation' , container2)    
    container2_items = get_items(container2)   
    for item in container2_items:                  
        doc1.append("items",item)   
    
    doc1.save(ignore_permissions= True)
    #doc2.delete(ignore_permissions= True)
    frappe.db.commit()


@frappe.whitelist(allow_guest = False)
def set_batches_from_bestvalue():
    from frappe.utils.data import add_days
    batches = frappe.db.sql(""" 
                SELECT best_value_date, name
                FROM `tabBatch`
                WHERE   (expiry_date = "" or expiry_date is null) 
                        AND best_value_date <> "" 
                        AND best_value_date is not null
            """, as_dict = 1)

    for batch in batches:
        doc = frappe.get_doc("Batch", batch.name)
        doc.expiry_date = add_days(doc.best_value_date, 14)
        doc.save()

    frappe.db.commit()


@frappe.whitelist(allow_guest = False)
def update_batch_clear_old():   
    frappe.db.sql(""" 
        UPDATE `tabItem Barcode`
        SET batch_no = ""
        WHERE batch_no LIKE "%%- OLD"      
    """)
    
    frappe.db.commit()


@frappe.whitelist(allow_guest = False)
def replace_old_batches():
    items = get_items()
    for item in items:
        new_batch = get_new_batch(item.item_code)
        if new_batch:            
            update_batch(item.item_code , new_batch)       

def get_items():
    items = frappe.db.sql (""" 
		SELECT  item_code
		FROM `tabItem`
		WHERE has_batch_no = 1
        ORDER BY modified DESC       
	""" , as_dict = True)

    return items

def update_batch(item_code , new_batch):   
    frappe.db.sql(""" 
        UPDATE `tabItem Barcode`
        SET batch_no = %s 
        WHERE parent = %s
        AND (batch_no LIKE "%%- OLD" or batch_no = "" or batch_no is null)      
    """, (new_batch , item_code))
    
    frappe.db.commit()
            

def get_new_batch(item_code):
    batch = frappe.db.sql (""" 
		SELECT  name 
		FROM `tabBatch`
		WHERE item = %s 
        AND disabled = 0
        AND expiry_date is not null AND expiry_date > CURRENT_TIMESTAMP
        AND    name not LIKE "%%- OLD"     
        ORDER BY expiry_date ASC
        LIMIT 1
	""" , item_code)

    if batch:
        return batch[0][0]
    else:
        return
    
    

