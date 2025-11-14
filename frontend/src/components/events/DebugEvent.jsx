/**
 * Debug Event Component
 *
 * Displays a debug message event in the event log.
 */
import React from 'react';
import PropTypes from 'prop-types';
import { DEBUG_LEVEL_COLORS, EVENT_ICONS } from '../../constants';

const DebugEvent = ({ event, timeStr }) => {
  // Use DEBUG_LEVEL_COLORS for level-specific colors
  const colors = DEBUG_LEVEL_COLORS[event.level] || DEBUG_LEVEL_COLORS.info;

  return (
    <div className={`${colors.bg} border ${colors.border} rounded-lg p-2`}>
      <div className="flex items-center gap-2">
        <div className="text-sm">{EVENT_ICONS.debug}</div>
        <div className={`text-xs ${colors.text}`}>{timeStr}</div>
        <div className={`text-xs ${colors.text}`}>{event.message}</div>
      </div>
    </div>
  );
};

DebugEvent.propTypes = {
  event: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    type: PropTypes.string.isRequired,
    level: PropTypes.oneOf(['info', 'warning', 'error', 'cooldown', 'probability']).isRequired,
    message: PropTypes.string.isRequired,
    timestamp: PropTypes.number.isRequired,
  }).isRequired,
  timeStr: PropTypes.string.isRequired,
};

export default DebugEvent;
