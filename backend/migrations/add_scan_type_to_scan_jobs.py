# migrations/add_scan_type_to_scan_jobs.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add scan_type column
    op.add_column('scan_jobs', 
        sa.Column('scan_type', 
                 sa.Enum('network_scan', 'service_enumeration', 'vulnerability_assessment', 
                         'credential_testing', 'web_scan', 'ssl_analysis', 'combined',
                         name='scantype'),
                 nullable=False,
                 server_default='network_scan')
    )
    
    # Add updated_at column
    op.add_column('scan_jobs',
        sa.Column('updated_at', 
                 sa.DateTime(),
                 nullable=True)
    )
    
    # Add error_message column
    op.add_column('scan_jobs',
        sa.Column('error_message',
                 sa.Text(),
                 nullable=True)
    )
    
    # Add config column
    op.add_column('scan_jobs',
        sa.Column('config',
                 sa.JSON(),
                 nullable=True)
    )
    
    # Rename insights to results
    op.alter_column('scan_jobs', 'insights', new_column_name='results')
    
    # Create index
    op.create_index('idx_scan_jobs_scan_type', 'scan_jobs', ['scan_type'])

def downgrade():
    op.drop_index('idx_scan_jobs_scan_type', 'scan_jobs')
    op.alter_column('scan_jobs', 'results', new_column_name='insights')
    op.drop_column('scan_jobs', 'config')
    op.drop_column('scan_jobs', 'error_message')
    op.drop_column('scan_jobs', 'updated_at')
    op.drop_column('scan_jobs', 'scan_type')