from django.core.management.base import BaseCommand
from products.models import Product

SERVICES = [
    # WORKSPACE SERVICES
    ('Workspace - Monthly',     6000,  'OTHER'),
    ('Workspace - Daily',        500,  'OTHER'),
    ('Workspace - Hourly',       100,  'OTHER'),
    
    # PRINTING
    ('Printing - Coloured',       15,  'PRINTING'),
    ('Printing - Black & White',  10,  'PRINTING'),
    
    # PHOTOCOPYING
    ('Photocopy - Coloured',      15,  'PRINTING'),
    ('Photocopy - Black & White', 10,  'PRINTING'),
    ('Photocopy - ID Coloured',   30,  'PRINTING'),
    ('Photocopy - ID Black',      20,  'PRINTING'),
    
    # SCANNING & TYPING
    ('Scanning (per page)',       20,  'SCANNING'),
    ('Typesetting (per page)',    40,  'DOCUMENTS'),
    
    # LAMINATION & BINDING
    ('Lamination (per paper)',    50,  'PRINTING'),
    ('Binding (0-50 pages)',      50,  'PRINTING'),
    ('Binding (51-75 pages)',     75,  'PRINTING'),
    ('Binding (76-100 pages)',   100,  'PRINTING'),
    ('Binding (100-125 pages)',  125,  'PRINTING'),
    
    # PHOTOS & IMAGES
    ('Passport Photos (8 pcs)',  150,  'DOCUMENTS'),
    ('Photo/Image A4 Glossy',    100,  'PRINTING'),
    ('Matte Glossy Paper',        50,  'PRINTING'),
    ('Glossy Sticker A4',        100,  'PRINTING'),
    
    # ENVELOPES
    ('A4 Envelopes',              15,  'DOCUMENTS'),
    ('A5 & B6 Envelopes',         10,  'DOCUMENTS'),
    
    # INTERNET & CV
    ('Browsing (per minute)',      1,  'INTERNET'),
    ('CV - Normal Format',       100,  'INTERNET'),
    ('CV - Professional',        200,  'INTERNET'),
    ('Converting/Editing Docs',   20,  'DOCUMENTS'),
    
    # E-CITIZEN & GOVERNMENT SERVICES
    ('Passport Application',     500,  'GOVERNMENT'),
    ('E-Citizen Registration',   100,  'GOVERNMENT'),
    ('DL Renewal',               150,  'GOVERNMENT'),
    ('Good Conduct',             150,  'GOVERNMENT'),
    ('Booking Inspection',       150,  'GOVERNMENT'),
    ('E-Tims Invoice',           100,  'GOVERNMENT'),
    ('Company Registration',    1000,  'GOVERNMENT'),
    ('Business Name Registration', 500, 'GOVERNMENT'),
    ('Birth/Marriage Certificates', 300, 'GOVERNMENT'),
    ('File Returns Nil',         100,  'GOVERNMENT'),
    ('File Returns (Employment Only)', 200, 'GOVERNMENT'),
    ('File Returns (Employment+)', 300, 'GOVERNMENT'),
    ('SHA Registration',         300,  'GOVERNMENT'),
    ('Other Online Application', 100,  'GOVERNMENT'),
    ('Vehicle Transfer',         300,  'GOVERNMENT'),
    ('KRA PIN Creation',         500,  'GOVERNMENT'),
    ('Email Creation',           200,  'INTERNET'),
]

class Command(BaseCommand):
    help = 'Seed the database with cyber cafe services from CYBER_SERVICES.docx'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        
        for name, price, category in SERVICES:
            obj, was_created = Product.objects.get_or_create(
                name=name,
                defaults={'price': price, 'category': category, 'is_service': True, 'active': True}
            )
            
            if was_created:
                created += 1
            else:
                # Update price and category for existing products
                if obj.price != price or obj.category != category:
                    obj.price = price
                    obj.category = category
                    obj.save()
                    updated += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'✅ Seeded {created} new services, updated {updated} existing services. '
            f'({len(SERVICES) - created - updated} already up-to-date)'
        ))
