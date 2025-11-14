/**
 * Error Event Component
 *
 * Displays an error event in the event log.
 */
import React from 'react';
import PropTypes from 'prop-types';
import { EVENT_COLORS, EVENT_ICONS } from '../../constants';

const ErrorEvent = ({ event, timeStr }) => {
  const colors = EVENT_COLORS.error;

  return (
    <div className={`${colors.bg} border ${colors.border} rounded-lg p-3`}>
      <div className="flex items-start gap-3">
        <div className={`flex-shrink-0 w-8 h-8 bg-red-500 rounded-full flex items-center justify-center text-sm`}>
          {EVENT_ICONS.error}
        </div>
        <div className="flex-1 min-w-0">
          <div className={`text-xs ${colors.text} mb-1`}>{timeStr} • Error</div>
          <div className={colors.text}>{event.message}</div>
        </div>
      </div>
    </div>
  );
};

ErrorEvent.propTypes = {
  event: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    type: PropTypes.string.isRequired,
    message: PropTypes.string.isRequired,
    timestamp: PropTypes.number.isRequired,
  }).isRequired,
  timeStr: PropTypes.string.isRequired,
};

export default ErrorEvent;
