import io
import os
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from xhtml2pdf import pisa
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse

def generate_invoice_pdf(order):
    """
    Generates a PDF invoice for the given order using xhtml2pdf.
    Returns the binary PDF content.
    """
    # Context for the template
    context = {
        'order': order,
        'items': order.items.all(),
    }
    
    # Render HTML template
    html_string = render_to_string('emails/invoice_pdf.html', context)
    
    # Generate PDF
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html_string.encode("UTF-8")), result)
    
    if not pdf.err:
        return result.getvalue()
    
    return None

def send_invoice_email(order, request=None):
    """
    Sends the invoice email to the customer with the PDF attached.
    Idempotent: Only sends if order.invoice_sent is False.
    """
    if order.invoice_sent:
        return True, "Invoice already sent."
        
    try:
        # Generate PDF
        pdf_content = generate_invoice_pdf(order)
        
        # Setup Email Context
        domain = 'urbnclothing.com'
        if request:
            domain = get_current_site(request).domain
            
        context = {
            'order': order,
            'customer_name': order.first_name or order.user.first_name or 'Customer',
            'domain': domain,
        }
        
        # Render Email Body
        html_content = render_to_string('emails/order_confirmation.html', context)
        text_content = strip_tags(render_to_string('emails/order_confirmation.txt', context))
        
        # Build Email
        subject = f"URBN Order Confirmed — #{order.order_number}"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [order.email]
        
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        
        # Attach PDF
        filename = f"URBN-Invoice-{order.order_number}.pdf"
        msg.attach(filename, pdf_content, 'application/pdf')
        
        # Send
        msg.send(fail_silently=False)
        
        # Mark as sent
        order.invoice_sent = True
        order.save(update_fields=['invoice_sent'])
        return True, "Invoice sent successfully."
        
    except Exception as e:
        print(f"Error sending invoice email for {order.order_number}: {e}")
        return False, str(e)
