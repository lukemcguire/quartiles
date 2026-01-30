"""add game tables

Revision ID: 7c818e95cae5
Revises: fe56fa70289e
Create Date: 2026-01-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '7c818e95cae5'
down_revision = 'fe56fa70289e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Player table
    op.create_table(
        'player',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('display_name', sa.String(length=50), nullable=False),
        sa.Column('device_fingerprint', sa.String(length=255), nullable=True),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_player_user_id_user')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_player')),
    )
    op.create_index('ix_player_user_id', 'player', ['user_id'])

    # Puzzle table
    op.create_table(
        'puzzle',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('tiles_json', sa.String(), nullable=False),
        sa.Column('quartile_words_json', sa.String(), nullable=False),
        sa.Column('valid_words_json', sa.String(), nullable=False),
        sa.Column('total_available_points', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_puzzle')),
        sa.UniqueConstraint('date', name=op.f('uq_puzzle_date')),
    )
    op.create_index('ix_puzzle_date', 'puzzle', ['date'])

    # GameSession table
    op.create_table(
        'game_session',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('puzzle_id', sa.Uuid(), nullable=False),
        sa.Column('player_id', sa.Uuid(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('solve_time_ms', sa.Integer(), nullable=True),
        sa.Column('final_score', sa.Integer(), nullable=False),
        sa.Column('hints_used', sa.Integer(), nullable=False),
        sa.Column('hint_penalty_ms', sa.Integer(), nullable=False),
        sa.Column('words_found_json', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['puzzle_id'], ['puzzle.id'], name=op.f('fk_game_session_puzzle_id_puzzle'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['player_id'], ['player.id'], name=op.f('fk_game_session_player_id_player'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_game_session')),
    )
    op.create_index('ix_game_session_puzzle_id', 'game_session', ['puzzle_id'])
    op.create_index('ix_game_session_player_id', 'game_session', ['player_id'])

    # LeaderboardEntry table
    op.create_table(
        'leaderboard_entry',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('puzzle_id', sa.Uuid(), nullable=False),
        sa.Column('player_id', sa.Uuid(), nullable=False),
        sa.Column('solve_time_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['puzzle_id'], ['puzzle.id'], name=op.f('fk_leaderboard_entry_puzzle_id_puzzle'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['player_id'], ['player.id'], name=op.f('fk_leaderboard_entry_player_id_player'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_leaderboard_entry')),
    )
    op.create_index('ix_leaderboard_entry_puzzle_id', 'leaderboard_entry', ['puzzle_id'])
    op.create_index('ix_leaderboard_entry_player_id', 'leaderboard_entry', ['player_id'])

    # QuartileCooldown table
    op.create_table(
        'quartile_cooldown',
        sa.Column('word', sa.String(length=20), nullable=False),
        sa.Column('last_used_date', sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint('word', name=op.f('pk_quartile_cooldown')),
    )


def downgrade() -> None:
    op.drop_table('quartile_cooldown')
    op.drop_index('ix_leaderboard_entry_player_id', table_name='leaderboard_entry')
    op.drop_index('ix_leaderboard_entry_puzzle_id', table_name='leaderboard_entry')
    op.drop_table('leaderboard_entry')
    op.drop_index('ix_game_session_player_id', table_name='game_session')
    op.drop_index('ix_game_session_puzzle_id', table_name='game_session')
    op.drop_table('game_session')
    op.drop_index('ix_puzzle_date', table_name='puzzle')
    op.drop_table('puzzle')
    op.drop_index('ix_player_user_id', table_name='player')
    op.drop_table('player')
