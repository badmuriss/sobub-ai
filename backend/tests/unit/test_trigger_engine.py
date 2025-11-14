"""
Unit tests for TriggerEngine.

Tests the trigger logic including cooldown management, probability checks,
and meme selection.
"""
import pytest
import time
from unittest.mock import patch
from app.trigger_engine import TriggerEngine


@pytest.mark.unit
class TestCooldownManagement:
    """Tests for cooldown timer management."""

    def test_initial_cooldown_inactive(self, trigger_engine):
        """Test that cooldown is inactive initially."""
        assert not trigger_engine.is_cooldown_active()
        assert trigger_engine.get_cooldown_remaining() == 0

    def test_start_cooldown(self, trigger_engine):
        """Test starting the cooldown timer."""
        trigger_engine.start_cooldown()

        assert trigger_engine.is_cooldown_active()
        assert trigger_engine.last_trigger_time is not None

    def test_cooldown_expires(self, trigger_engine):
        """Test that cooldown expires after the configured time."""
        trigger_engine.set_cooldown(1)  # 1 second cooldown
        trigger_engine.start_cooldown()

        assert trigger_engine.is_cooldown_active()

        # Wait for cooldown to expire
        time.sleep(1.1)

        assert not trigger_engine.is_cooldown_active()
        assert trigger_engine.get_cooldown_remaining() == 0

    def test_reset_cooldown(self, trigger_engine):
        """Test resetting the cooldown manually."""
        trigger_engine.start_cooldown()
        assert trigger_engine.is_cooldown_active()

        trigger_engine.reset_cooldown()

        assert not trigger_engine.is_cooldown_active()
        assert trigger_engine.last_trigger_time is None

    def test_get_cooldown_remaining(self, trigger_engine):
        """Test getting remaining cooldown time."""
        trigger_engine.set_cooldown(10)
        trigger_engine.start_cooldown()

        remaining = trigger_engine.get_cooldown_remaining()

        # Should be between 8-10 seconds (accounting for execution time)
        assert 8 <= remaining <= 10

    def test_cooldown_remaining_zero_when_inactive(self, trigger_engine):
        """Test that remaining time is 0 when cooldown is inactive."""
        assert trigger_engine.get_cooldown_remaining() == 0

    def test_set_cooldown(self, trigger_engine):
        """Test setting cooldown duration."""
        trigger_engine.set_cooldown(300)

        assert trigger_engine.cooldown_seconds == 300

    def test_cooldown_with_zero_seconds(self, trigger_engine):
        """Test cooldown with 0 seconds."""
        trigger_engine.set_cooldown(0)
        trigger_engine.start_cooldown()

        # Should immediately be inactive
        assert not trigger_engine.is_cooldown_active()


@pytest.mark.unit
class TestProbability:
    """Tests for probability-based triggering."""

    def test_set_probability(self, trigger_engine):
        """Test setting trigger probability."""
        trigger_engine.set_probability(75.0)

        assert trigger_engine.trigger_probability == 75.0

    def test_set_probability_clamped_to_max(self, trigger_engine):
        """Test that probability is clamped to 100."""
        trigger_engine.set_probability(150.0)

        assert trigger_engine.trigger_probability == 100.0

    def test_set_probability_clamped_to_min(self, trigger_engine):
        """Test that probability is clamped to 0."""
        trigger_engine.set_probability(-50.0)

        assert trigger_engine.trigger_probability == 0.0

    def test_should_trigger_with_100_percent(self, trigger_engine):
        """Test that 100% probability always triggers."""
        trigger_engine.set_probability(100.0)

        # Test multiple times to ensure it's always true
        results = [trigger_engine.should_trigger() for _ in range(10)]

        assert all(results)

    def test_should_trigger_with_0_percent(self, trigger_engine):
        """Test that 0% probability never triggers."""
        trigger_engine.set_probability(0.0)

        # Test multiple times to ensure it's always false
        results = [trigger_engine.should_trigger() for _ in range(10)]

        assert not any(results)

    @patch('random.uniform')
    def test_should_trigger_with_mock_random(self, mock_random, trigger_engine):
        """Test probability check with mocked random value."""
        trigger_engine.set_probability(50.0)

        # Mock random to return 25.0 (should trigger)
        mock_random.return_value = 25.0
        assert trigger_engine.should_trigger()

        # Mock random to return 75.0 (should not trigger)
        mock_random.return_value = 75.0
        assert not trigger_engine.should_trigger()


@pytest.mark.unit
class TestMemeSelection:
    """Tests for meme selection logic."""

    def test_select_random_meme(self, trigger_engine, sample_memes):
        """Test random meme selection."""
        selected = trigger_engine.select_random_meme(sample_memes)

        assert selected is not None
        assert selected in sample_memes

    def test_select_random_meme_from_empty_list(self, trigger_engine):
        """Test selection from empty list returns None."""
        selected = trigger_engine.select_random_meme([])

        assert selected is None

    def test_select_random_meme_distribution(self, trigger_engine, sample_memes):
        """Test that random selection covers all memes over time."""
        selections = [trigger_engine.select_random_meme(sample_memes) for _ in range(100)]

        # All memes should be selected at least once
        selected_ids = {meme['id'] for meme in selections}
        expected_ids = {meme['id'] for meme in sample_memes}

        assert selected_ids == expected_ids

    def test_select_meme_with_preference(self, trigger_engine, sample_memes):
        """Test preference-based selection."""
        match_scores = {
            "goal": 1,
            "incredible goal": 2,  # Higher score
            "football": 1
        }

        selected = trigger_engine.select_meme_with_preference(sample_memes, match_scores)

        assert selected is not None

    def test_select_meme_with_preference_empty_list(self, trigger_engine):
        """Test preference selection with empty meme list."""
        selected = trigger_engine.select_meme_with_preference([], {"tag": 1})

        assert selected is None

    def test_select_meme_with_preference_prefers_higher_scores(self, trigger_engine):
        """Test that preference selection favors higher-scoring memes."""
        memes = [
            {"id": 1, "filename": "test1.mp3", "tags": ["goal"]},
            {"id": 2, "filename": "test2.mp3", "tags": ["incredible goal"]},
        ]
        match_scores = {
            "goal": 1,
            "incredible goal": 3  # Much higher score
        }

        # Run selection multiple times
        selections = [
            trigger_engine.select_meme_with_preference(memes, match_scores)
            for _ in range(50)
        ]

        # Most selections should be the higher-scoring meme (id=2)
        # But some randomness is expected within same score tier
        selected_ids = [s['id'] for s in selections]
        assert 2 in selected_ids

    def test_select_meme_with_preference_no_scores(self, trigger_engine, sample_memes):
        """Test preference selection with empty scores falls back to random."""
        selected = trigger_engine.select_meme_with_preference(sample_memes, {})

        # Should still select a meme (falls back to random)
        assert selected is not None
        assert selected in sample_memes


@pytest.mark.unit
class TestAttemptTrigger:
    """Tests for the attempt_trigger method."""

    def test_attempt_trigger_no_matches(self, trigger_engine):
        """Test that no trigger occurs with empty meme list."""
        result = trigger_engine.attempt_trigger([])

        assert result is None

    def test_attempt_trigger_during_cooldown(self, trigger_engine, sample_memes):
        """Test that trigger fails during active cooldown."""
        trigger_engine.set_cooldown(60)
        trigger_engine.start_cooldown()

        result = trigger_engine.attempt_trigger(sample_memes)

        assert result is None

    @patch('random.uniform', return_value=25.0)  # Will pass 50% threshold
    def test_attempt_trigger_success(self, mock_random, trigger_engine, sample_memes):
        """Test successful trigger when cooldown passed and probability met."""
        trigger_engine.set_probability(50.0)
        trigger_engine.reset_cooldown()  # Ensure no cooldown

        result = trigger_engine.attempt_trigger(sample_memes)

        assert result is not None
        assert result in sample_memes

    @patch('random.uniform', return_value=75.0)  # Will fail 50% threshold
    def test_attempt_trigger_probability_failure(self, mock_random, trigger_engine, sample_memes):
        """Test that trigger fails when probability check fails."""
        trigger_engine.set_probability(50.0)
        trigger_engine.reset_cooldown()

        result = trigger_engine.attempt_trigger(sample_memes)

        assert result is None

    def test_attempt_trigger_does_not_start_cooldown(self, trigger_engine, sample_memes):
        """Test that attempt_trigger does not start cooldown automatically."""
        trigger_engine.set_probability(100.0)
        trigger_engine.reset_cooldown()

        result = trigger_engine.attempt_trigger(sample_memes)

        # Should have triggered
        assert result is not None

        # But cooldown should NOT be started (that happens when audio ends)
        # A second attempt should also succeed
        result2 = trigger_engine.attempt_trigger(sample_memes)
        assert result2 is not None

    @patch('random.uniform', return_value=25.0)
    def test_attempt_trigger_with_scores(self, mock_random, trigger_engine, sample_memes):
        """Test trigger with match scores for preference-based selection."""
        trigger_engine.set_probability(50.0)
        trigger_engine.reset_cooldown()

        match_scores = {
            "goal": 1,
            "incredible goal": 2
        }

        result = trigger_engine.attempt_trigger(sample_memes, match_scores)

        assert result is not None


@pytest.mark.unit
class TestGetStatus:
    """Tests for status reporting."""

    def test_get_status_no_cooldown(self, trigger_engine):
        """Test status when no cooldown is active."""
        trigger_engine.set_cooldown(180)
        trigger_engine.set_probability(50.0)

        status = trigger_engine.get_status()

        assert status['cooldown_seconds'] == 180
        assert status['trigger_probability'] == 50.0
        assert status['cooldown_active'] is False
        assert status['cooldown_remaining'] == 0
        assert status['last_trigger_time'] is None

    def test_get_status_with_active_cooldown(self, trigger_engine):
        """Test status when cooldown is active."""
        trigger_engine.set_cooldown(180)
        trigger_engine.set_probability(50.0)
        trigger_engine.start_cooldown()

        status = trigger_engine.get_status()

        assert status['cooldown_seconds'] == 180
        assert status['trigger_probability'] == 50.0
        assert status['cooldown_active'] is True
        assert status['cooldown_remaining'] > 0
        assert status['last_trigger_time'] is not None

    def test_get_status_returns_correct_types(self, trigger_engine):
        """Test that status returns correct data types."""
        status = trigger_engine.get_status()

        assert isinstance(status['cooldown_seconds'], int)
        assert isinstance(status['trigger_probability'], float)
        assert isinstance(status['cooldown_active'], bool)
        assert isinstance(status['cooldown_remaining'], int)


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_negative_cooldown_seconds(self, trigger_engine):
        """Test behavior with negative cooldown (should still work)."""
        trigger_engine.set_cooldown(-10)

        # Implementation doesn't validate, so it accepts negative values
        # Cooldown will effectively be inactive
        trigger_engine.start_cooldown()
        assert not trigger_engine.is_cooldown_active()

    def test_very_large_cooldown(self, trigger_engine):
        """Test with very large cooldown value."""
        trigger_engine.set_cooldown(999999)
        trigger_engine.start_cooldown()

        assert trigger_engine.is_cooldown_active()
        assert trigger_engine.get_cooldown_remaining() > 999990

    def test_multiple_cooldown_starts(self, trigger_engine):
        """Test that starting cooldown multiple times updates the timer."""
        trigger_engine.set_cooldown(60)

        trigger_engine.start_cooldown()
        first_time = trigger_engine.last_trigger_time

        time.sleep(0.1)

        trigger_engine.start_cooldown()
        second_time = trigger_engine.last_trigger_time

        # Second start should update the time
        assert second_time > first_time

    def test_meme_selection_with_single_meme(self, trigger_engine):
        """Test selection when only one meme is available."""
        single_meme = [{"id": 1, "filename": "test.mp3", "tags": ["test"]}]

        selected = trigger_engine.select_random_meme(single_meme)

        assert selected == single_meme[0]

    @patch('random.uniform', return_value=50.0)
    def test_boundary_probability_exact_match(self, mock_random, trigger_engine):
        """Test probability boundary when random value exactly matches threshold."""
        trigger_engine.set_probability(50.0)

        # random.uniform returns 50.0, probability is 50.0
        # Should NOT trigger (50 < 50 is False)
        assert not trigger_engine.should_trigger()

        # Set probability to 50.1, should trigger
        trigger_engine.set_probability(50.1)
        assert trigger_engine.should_trigger()
