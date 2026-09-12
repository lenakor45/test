from alembic import op
import sqlalchemy as sa

revision='0001'; down_revision=None; branch_labels=None; depends_on=None

def upgrade():
    op.create_table('parents',sa.Column('id',sa.Integer,primary_key=True),sa.Column('name',sa.String(200),nullable=False),sa.Column('contacts',sa.Text,nullable=False),sa.Column('hourly_rate_kopecks',sa.BigInteger,nullable=False),sa.Column('active',sa.Boolean,nullable=False),sa.Column('created_at',sa.DateTime,nullable=False))
    op.create_table('students',sa.Column('id',sa.Integer,primary_key=True),sa.Column('parent_id',sa.Integer,sa.ForeignKey('parents.id',ondelete='CASCADE'),nullable=False),sa.Column('name',sa.String(200),nullable=False),sa.Column('subject',sa.String(200),nullable=False),sa.Column('duration_minutes',sa.Integer,nullable=False),sa.Column('active',sa.Boolean,nullable=False))
    op.create_table('recurring_schedules',sa.Column('id',sa.Integer,primary_key=True),sa.Column('student_id',sa.Integer,sa.ForeignKey('students.id',ondelete='CASCADE'),nullable=False),sa.Column('weekday',sa.Integer,nullable=False),sa.Column('start_time',sa.Time,nullable=False),sa.Column('duration_minutes',sa.Integer,nullable=False),sa.Column('start_date',sa.Date,nullable=False),sa.Column('end_date',sa.Date),sa.Column('active',sa.Boolean,nullable=False))
    op.create_table('lessons',sa.Column('id',sa.Integer,primary_key=True),sa.Column('student_id',sa.Integer,sa.ForeignKey('students.id',ondelete='RESTRICT'),nullable=False),sa.Column('schedule_id',sa.Integer,sa.ForeignKey('recurring_schedules.id',ondelete='SET NULL')),sa.Column('starts_at',sa.DateTime,nullable=False),sa.Column('duration_minutes',sa.Integer,nullable=False),sa.Column('status',sa.String(20),nullable=False),sa.Column('hourly_rate_kopecks',sa.BigInteger,nullable=False),sa.Column('charged_kopecks',sa.BigInteger),sa.Column('note',sa.Text,nullable=False),sa.UniqueConstraint('student_id','starts_at',name='uq_lesson_student_start'))
    op.create_index('ix_lessons_starts_at','lessons',['starts_at'])
    op.create_table('payments',sa.Column('id',sa.Integer,primary_key=True),sa.Column('parent_id',sa.Integer,sa.ForeignKey('parents.id',ondelete='CASCADE'),nullable=False),sa.Column('amount_kopecks',sa.BigInteger,nullable=False),sa.Column('paid_on',sa.Date,nullable=False),sa.Column('comment',sa.Text,nullable=False),sa.Column('created_at',sa.DateTime,nullable=False))
    op.create_table('financial_entries',sa.Column('id',sa.Integer,primary_key=True),sa.Column('parent_id',sa.Integer,sa.ForeignKey('parents.id',ondelete='CASCADE'),nullable=False),sa.Column('lesson_id',sa.Integer,sa.ForeignKey('lessons.id',ondelete='CASCADE'),unique=True),sa.Column('amount_kopecks',sa.BigInteger,nullable=False),sa.Column('created_at',sa.DateTime,nullable=False),sa.Column('description',sa.String(300),nullable=False))

def downgrade():
    op.drop_table('financial_entries'); op.drop_table('payments'); op.drop_index('ix_lessons_starts_at'); op.drop_table('lessons'); op.drop_table('recurring_schedules'); op.drop_table('students'); op.drop_table('parents')
