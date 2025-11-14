/**
 * Event Components Index
 *
 * This module exports all event components and provides a strategy pattern
 * implementation for rendering events based on type.
 */

import TranscriptionEvent from './TranscriptionEvent';
import MatchEvent from './MatchEvent';
import TriggerEvent from './TriggerEvent';
import DebugEvent from './DebugEvent';
import ErrorEvent from './ErrorEvent';
import { EVENT_TYPES } from '../../constants';

/**
 * Event renderer registry (Strategy Pattern)
 *
 * Maps event types to their corresponding React components.
 * This follows the Open/Closed Principle: open for extension (add new
 * event types), closed for modification (no need to change existing code).
 */
export const EVENT_RENDERERS = {
  [EVENT_TYPES.TRANSCRIPTION]: TranscriptionEvent,
  [EVENT_TYPES.MATCH]: MatchEvent,
  [EVENT_TYPES.TRIGGER]: TriggerEvent,
  [EVENT_TYPES.DEBUG]: DebugEvent,
  [EVENT_TYPES.ERROR]: ErrorEvent,
};

/**
 * Get the appropriate event renderer component for an event type
 *
 * @param {string} eventType - The event type
 * @returns {React.Component|null} - The component to render the event, or null
 */
export const getEventRenderer = (eventType) => {
  return EVENT_RENDERERS[eventType] || null;
};

/**
 * Render an event using the appropriate component
 *
 * @param {Object} event - The event object
 * @param {string} timeStr - Formatted time string
 * @returns {React.Element|null} - Rendered event or null
 */
export const renderEvent = (event, timeStr) => {
  const EventComponent = getEventRenderer(event.type);

  if (!EventComponent) {
    console.warn(`Unknown event type: ${event.type}`);
    return null;
  }

  return <EventComponent key={event.id} event={event} timeStr={timeStr} />;
};

// Export individual components for direct use if needed
export {
  TranscriptionEvent,
  MatchEvent,
  TriggerEvent,
  DebugEvent,
  ErrorEvent,
};
