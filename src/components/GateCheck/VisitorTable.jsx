import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../Auth/api';
import {
  Users, MoreVertical, Phone, Clock, User, Calendar, MapPin, Car, Mail,
  Building2, Loader2, X, Tag, FileText, RefreshCw, Lock
} from 'lucide-react';

const VisitorTable = ({
  filteredVisitors,
  showRecurring,
  onVisitorUpdate,
  getStatusColor,
  getStatusDot,
  getPassTypeLabel,
  getCategoryLabel
}) => {
  const [loadingActions, setLoadingActions] = useState({});
  const [openDropdown, setOpenDropdown] = useState(null);
  const [otpModal, setOtpModal] = useState({
    isOpen: false,
    visitor: null,
    type: '', // 'checkin' or 'checkout'
    otp: '',
    error: '',
    isVerifying: false
  });
  const [rescheduleModal, setRescheduleModal] = useState({
    isOpen: false,
    visitor: null,
    newDate: '',
    newTime: '',
    errors: {}
  });
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  // Memoized function to check if visiting time is in the past
  const isVisitingTimeInPast = useCallback((visitingDate, visitingTime) => {
    if (!visitingDate) return false;
    
    const now = new Date();
    const visitDate = new Date(visitingDate);
    
    if (visitingTime) {
      const [hours, minutes] = visitingTime.split(':');
      visitDate.setHours(parseInt(hours), parseInt(minutes), 0);
    } else {
      // If no time specified, consider end of day
      visitDate.setHours(23, 59, 59);
    }
    
    return visitDate < now;
  }, []);

  // Handle OTP Modal
  const handleOtpAction = (visitor, actionType) => {
    setOtpModal({
      isOpen: true,
      visitor: visitor,
      type: actionType,
      otp: '',
      error: '',
      isVerifying: false
    });
    setOpenDropdown(null);
  };

  const closeOtpModal = () => {
    setOtpModal({
      isOpen: false,
      visitor: null,
      type: '',
      otp: '',
      error: '',
      isVerifying: false
    });
  };

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    
    if (!otpModal.otp.trim()) {
      setOtpModal(prev => ({ ...prev, error: 'Please enter OTP' }));
      return;
    }

    if (otpModal.otp.length !== 6) {
      setOtpModal(prev => ({ ...prev, error: 'OTP must be 6 digits' }));
      return;
    }

    setOtpModal(prev => ({ ...prev, isVerifying: true, error: '' }));
    const passId = otpModal.visitor.pass_id;
    console.log(passId);
    try {
      let response;
      let otpPayload = {
        otp: otpModal.otp,
        action: otpModal.type == "checkin" ?"entry":"exit",
      };
console.log(otpPayload)
      console.log("inside try block ")
        console.log("otp modal type ",otpModal.type)

      if (otpModal.type === 'checkin') {
        // Call entry OTP verification endpoint
        response = await api.visitors.verifyEntryOtp(passId, otpPayload);
      } else if (otpModal.type === 'checkout') {

        console.log("excuting checkout  ")
        // Call exit OTP verification endpoint
        
        response = await api.visitors.verifyExitOtp(passId, otpPayload);
        console.log(response)
      }

      // Check if OTP is valid
      if (response && response.status === 200) {
        // OTP is valid
        const actionType = otpModal.type;
        const newStatus = actionType === 'entry' ? 'CHECKED_IN' : 'CHECKED_OUT';
        
        // Show success message
        alert(`Valid OTP! Visitor ${actionType === 'entry' ? 'entered' : 'exit'} successfully.`);
        
        // Update visitor status
        if (onVisitorUpdate) {
          onVisitorUpdate(passId, newStatus, actionType);
        }
        
        // Close modal
        closeOtpModal();
      } else {
        throw new Error('Invalid OTP');
      }
    } catch (error) {
      console.error(`Failed to verify ${otpModal.type} OTP:`, error);
      console.log(error);
      setOtpModal(prev => ({ 
        ...prev, 
        error: 'Invalid OTP. Please try again.',
        isVerifying: false 
      }));
    } finally {
      setOtpModal(prev => ({ ...prev, isVerifying: false }));
    }
  };

  const handleStatusUpdate = async (visitorId, newStatus, actionType) => {
    // For checkin and checkout, show OTP modal instead of direct API call
    if (actionType === 'checkin' || actionType === 'checkout') {
      const visitor = filteredVisitors.find(v => v.id === visitorId);
      handleOtpAction(visitor, actionType);
      return;
    }

    setLoadingActions(prev => ({ ...prev, [`${visitorId}-${actionType}`]: true }));
    
    try {
      let response;
      switch (actionType) {
        case 'approve':
          response = await api.visitors.approve(visitorId);
          break;
        case 'reject':
          response = await api.visitors.reject(visitorId);
          break;
        default:
          throw new Error(`Unknown action type: ${actionType}`);
      }

      // Check if response is successful (status 200-299)
      if (response && (response.status === 200)) {
        console.log('Calling onVisitorUpdate with:', { visitorId, newStatus, actionType });
        
        if (onVisitorUpdate) {
          onVisitorUpdate(visitorId, newStatus, actionType);
        } else {
          console.warn('onVisitorUpdate callback is not provided!');
        }
      } else {
        throw new Error('API request failed');
      }
    } catch (error) {
      console.error(`Failed to ${actionType} visitor:`, error);
      alert(`Failed to ${actionType} visitor. Please try again.`);
    } finally {
      setLoadingActions(prev => ({ ...prev, [`${visitorId}-${actionType}`]: false }));
    }
  };

  const handlePassGeneration = async (visitorId, passType) => {
    setLoadingActions(prev => ({ ...prev, [`${visitorId}-${passType}`]: true }));
    setOpenDropdown(null);
    console.log("manual clicked");
    
    try {
      const visitorData = filteredVisitors.find(visitor => visitor.id === visitorId);
      if (passType === 'manual') {
        navigate('/manual-pass', { state: { visitor: visitorData } });
      } else if (passType === 'qr') {
        navigate('/qr-pass', { state: { visitor: visitorData } });
      }
    } catch (error) {
      alert(`Failed to generate ${passType === 'manual' ? 'manual' : 'qr'} pass. Please try again.`);
    } finally {
      setLoadingActions(prev => ({ ...prev, [`${visitorId}-${passType}`]: false }));
    }
  };

  const handleReschedule = (visitor) => {
    setRescheduleModal({
      isOpen: true,
      visitor: visitor,
      newDate: '',
      newTime: '',
      errors: {}
    });
    setOpenDropdown(null);
  };

  const validateRescheduleForm = useCallback(() => {
    const errors = {};
    const now = new Date();

    if (!rescheduleModal.newDate) {
      errors.newDate = 'Date is required';
    }

    if (!rescheduleModal.newTime) {
      errors.newTime = 'Time is required';
    }

    if (rescheduleModal.newDate && rescheduleModal.newTime) {
      // Only allow today or future date, but time must be in the future if today
      const selectedDate = new Date(rescheduleModal.newDate);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      selectedDate.setHours(0, 0, 0, 0);
      const selectedDateTime = new Date(`${rescheduleModal.newDate}T${rescheduleModal.newTime}`);
      if (selectedDate < today) {
        errors.newDate = 'Date cannot be in the past';
      } else if (selectedDate.getTime() === today.getTime() && selectedDateTime <= now) {
        errors.newTime = 'Time must be in the future for today';
      } else if (selectedDateTime <= now) {
        errors.newTime = 'Date and time must be in the future';
      }
    }

    return errors;
  }, [rescheduleModal.newDate, rescheduleModal.newTime]);

  const handleRescheduleSubmit = async (e) => {
    e.preventDefault();
    
    const errors = validateRescheduleForm();
    if (Object.keys(errors).length > 0) {
      setRescheduleModal(prev => ({ ...prev, errors }));
      return;
    }

    const visitorId = rescheduleModal.visitor.id;
    setLoadingActions(prev => ({ ...prev, [`${visitorId}-reschedule`]: true }));

    try {
      // Prepare the payload
      const payload = {
        new_date: rescheduleModal.newDate,
        new_time: rescheduleModal.newTime + ':00' // Add seconds to match HH:MM:SS format
      };

      // Make API call to reschedule
      const response = await api.visitors.reschedule(visitorId, payload);

      // If response is axios/fetch, handle accordingly
      let data;
      if (response && response.data) {
        data = response.data;
      } else {
        data = response;
      }

      // Update the visitor in the local state
      if (onVisitorUpdate) {
        onVisitorUpdate(visitorId, 'PENDING', 'reschedule', {
          visiting_date: data.new_date || payload.new_date,
          visiting_time: (data.new_time || payload.new_time).substring(0, 5) // Remove seconds for display (HH:MM format)
        });
      }

      // Close modal and show success message
      setRescheduleModal({
        isOpen: false,
        visitor: null,
        newDate: '',
        newTime: '',
        errors: {}
      });

      alert('Visitor successfully rescheduled!');
    } catch (error) {
      console.error('Failed to reschedule visitor:', error);
      alert(`Failed to reschedule visitor: ${error.message}`);
    } finally {
      setLoadingActions(prev => ({ ...prev, [`${visitorId}-reschedule`]: false }));
    }
  };

  const closeRescheduleModal = () => {
    setRescheduleModal({
      isOpen: false,
      visitor: null,
      newDate: '',
      newTime: '',
      errors: {}
    });
  };

  // Helper to check if visiting_date is today, in past, or in future
  const isVisitingDateToday = (visitingDate) => {
    if (!visitingDate) return false;
    const today = new Date();
    const visitDate = new Date(visitingDate);
    return (
      visitDate.getFullYear() === today.getFullYear() &&
      visitDate.getMonth() === today.getMonth() &&
      visitDate.getDate() === today.getDate()
    );
  };
  const isVisitingDatePast = (visitingDate) => {
    if (!visitingDate) return false;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const visitDate = new Date(visitingDate);
    visitDate.setHours(0, 0, 0, 0);
    return visitDate < today;
  };
  const isVisitingDateFuture = (visitingDate) => {
    if (!visitingDate) return false;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const visitDate = new Date(visitingDate);
    visitDate.setHours(0, 0, 0, 0);
    return visitDate > today;
  };

  // Memoized function to get action buttons (driven by backend status)
  const getActionButtons = useCallback((visitor) => {
    const buttons = [];

    // If logs are present, use the first log's action as the authoritative source
    const logs = visitor.logs || [];
    if (logs.length > 0) {
      const firstAction = String(logs[0].action || '').toUpperCase();
      if (firstAction === 'EXIT') {
        buttons.push(
          <div key="completed" className="px-2 py-1 text-xs text-gray-600 border border-gray-200 rounded bg-gray-50">
            Completed
          </div>
        );
        return buttons;
      }
      if (firstAction === 'ENTRY') {
        buttons.push(
          <button
            key="checkout"
            onClick={() => handleStatusUpdate(visitor.id, 'CHECKED_OUT', 'checkout')}
            className="px-2 py-1 text-xs text-gray-600 border border-gray-600 rounded hover:text-gray-900 hover:bg-gray-50"
          >
            Check Out
          </button>
        );
        return buttons;
      }
    }

    const status = (visitor.status || '').toUpperCase();
    const completedStatuses = ['CHECKED_OUT', 'COMPLETED', 'VISITED'];

    // If backend status indicates completion, show Completed badge
    if (completedStatuses.includes(status)) {
      buttons.push(
        <div key="completed" className="px-2 py-1 text-xs text-gray-600 border border-gray-200 rounded bg-gray-50">
          Completed
        </div>
      );
      return buttons;
    }

    // PENDING status: Show Approve/Reject for today, Reschedule for past (only if not CHECKED_IN), Check In for future
    if (visitor.status === 'PENDING') {
      if (isVisitingDateToday(visitor.visiting_date)) {
        buttons.push(
          <button
            key="approve"
            onClick={() => handleStatusUpdate(visitor.id, 'APPROVED', 'approve')}
            disabled={loadingActions[`${visitor.id}-approve`]}
            className="px-2 py-1 text-xs text-green-600 border border-green-600 rounded hover:text-green-900 hover:bg-green-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loadingActions[`${visitor.id}-approve`] ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              'Approve'
            )}
          </button>
        );
        buttons.push(
          <button
            key="reject"
            onClick={() => handleStatusUpdate(visitor.id, 'REJECTED', 'reject')}
            disabled={loadingActions[`${visitor.id}-reject`]}
            className="px-2 py-1 text-xs text-red-600 border border-red-600 rounded hover:text-red-900 hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loadingActions[`${visitor.id}-reject`] ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              'Reject'
            )}
          </button>
        );
      } else if (isVisitingDatePast(visitor.visiting_date)) {
        // Only show reschedule button if visitor is not CHECKED_IN
        if (visitor.status !== 'CHECKED_IN') {
          buttons.push(
            <button
              key="reschedule"
              onClick={() => handleReschedule(visitor)}
              disabled={loadingActions[`${visitor.id}-reschedule`]}
              className="px-2 py-1 text-xs text-orange-600 border border-orange-600 rounded hover:text-orange-900 hover:bg-orange-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loadingActions[`${visitor.id}-reschedule`] ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <>
                  <RefreshCw className="inline w-3 h-3 mr-1" />
                  Reschedule
                </>
              )}
            </button>
          );
        }
      } else if (isVisitingDateFuture(visitor.visiting_date)) {
        buttons.push(
          <button
            key="checkin"
            onClick={() => handleStatusUpdate(visitor.id, 'CHECKED_IN', 'checkin')}
            className="px-2 py-1 text-xs text-blue-600 border border-blue-600 rounded hover:text-blue-900 hover:bg-blue-50"
          >
            Check In
          </button>
        );
      }
    }

    // APPROVED status: Show Check In button
    if (visitor.status === 'APPROVED') {
      buttons.push(
        <button
          key="checkin"
          onClick={() => handleStatusUpdate(visitor.id, 'CHECKED_IN', 'checkin')}
          className="px-2 py-1 text-xs text-blue-600 border border-blue-600 rounded hover:text-blue-900 hover:bg-blue-50"
        >
          Check In
        </button>
      );
    }

    // CHECKED_IN status: Show Check Out button
    if (visitor.status === 'CHECKED_IN') {
      buttons.push(
        <button
          key="checkout"
          onClick={() => handleStatusUpdate(visitor.id, 'CHECKED_OUT', 'checkout')}
          className="px-2 py-1 text-xs text-gray-600 border border-gray-600 rounded hover:text-gray-900 hover:bg-gray-50"
        >
          Check Out
        </button>
      );
    }

    // CHECKED_OUT status: Show nothing (empty space)
    // REJECTED status: No buttons (stays rejected)

    return buttons;
  }, [loadingActions, handleStatusUpdate]);

  const toggleDropdown = (visitorId) => {
    setOpenDropdown(openDropdown === visitorId ? null : visitorId);
  };

  return (
    <>
      <div className="px-6 py-4">
        <div className="overflow-hidden bg-transparent border border-gray-200 rounded-lg shadow">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                    Visitor Details
                  </th>
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                    Category
                  </th>
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                    Contact
                  </th>
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                    Visit Info
                  </th>
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-transparent divide-y divide-gray-200">
                {filteredVisitors.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                      <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                      <p className="text-lg font-medium">No visitors found</p>
                    </td>
                  </tr>
                ) : (
                  filteredVisitors.map((visitor) => (
                    <tr key={visitor.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 w-10 h-10">
                            <div className="flex items-center justify-center w-10 h-10 bg-purple-100 rounded-full">
                              <User className="w-5 h-5 text-purple-800" />
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="flex flex-col text-sm font-medium text-gray-900">
                              {visitor.visitor_name}
                              {(visitor.passId || visitor.pass_id) && (
                                <span className="text-xs text-gray-400">
                                  ID: {visitor.passId || visitor.pass_id}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">
                          {visitor.category_details.name && (
                            <span className="px-2 py-1 ml-2 text-xs text-blue-800 bg-blue-100 rounded-full">
                              {getCategoryLabel(visitor.category_details.name)}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center text-sm text-gray-900">
                          <Phone className="w-4 h-4 mr-2 text-gray-400" />
                          {visitor.mobile_number}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          <div className="flex items-center mb-1">
                            <Calendar className="w-4 h-4 mr-2 text-gray-400" />
                            {new Date(visitor.visiting_date).toLocaleDateString()}
                          </div>
                          {visitor.visiting_time && (
                            <div className="flex items-center mb-1">
                              <Clock className="w-4 h-4 mr-2 text-gray-400" />
                              {visitor.visiting_time}
                            </div>
                          )}
                          {visitor.purpose_of_visit && (
                            <div className="mt-1 text-xs text-gray-500">
                              {visitor.purpose_of_visit}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {!showRecurring && (() => {
                          // If logs indicate the visitor completed the visit (first action is EXIT), show VISITED
                          const logs = visitor.logs || [];
                          const firstAction = logs.length > 0 ? String(logs[0].action || '').toUpperCase() : '';
                          const displayStatus = firstAction === 'EXIT' ? 'VISITED' : (visitor.status || '');
                          return (
                            <div className="flex items-center">
                              <div className={`w-2 h-2 rounded-full mr-2 ${getStatusDot(displayStatus)}`}></div>
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(displayStatus)}`}>
                                {String(displayStatus).replace('_', ' ')}
                              </span>
                            </div>
                          );
                        })()}
                        {showRecurring && (
                          <div className="text-sm text-gray-500">
                            <div>Active until:</div>
                            <div>{visitor.valid_until ? new Date(visitor.valid_until).toLocaleDateString() : 'No expiry'}</div>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm font-medium text-right whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          {!showRecurring && getActionButtons(visitor)}
                          <div className="relative" ref={dropdownRef}>
                            <button
                              onClick={() => toggleDropdown(visitor.id)}
                              className="p-1 text-gray-400 rounded-md hover:text-gray-600 hover:bg-gray-100"
                            >
                              <MoreVertical className="w-4 h-4" />
                            </button>
                            {openDropdown === visitor.id && (
                              <div className="absolute right-0 z-10 w-48 py-1 mt-2 bg-white border border-gray-200 rounded-md shadow-lg">
                                <button
                                  onClick={() => handlePassGeneration(visitor.id, 'manual')}
                                  disabled={loadingActions[`${visitor.id}-manual`]}
                                  className="flex items-center w-full px-4 py-2 text-sm text-purple-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                  {loadingActions[`${visitor.id}-manual`] ? (
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                  ) : (
                                    <FileText className="w-4 h-4 mr-2" />
                                  )}
                                  Manual Pass
                                </button>
                                <button
                                  onClick={() => handlePassGeneration(visitor.id, 'qr')}
                                  disabled={loadingActions[`${visitor.id}-qr`]}
                                  className="flex items-center w-full px-4 py-2 text-sm text-purple-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                  {loadingActions[`${visitor.id}-qr`] ? (
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                  ) : (
                                    <div className="w-4 h-4 mr-2 border border-gray-400 rounded-sm">
                                      <div className="w-full h-full bg-gray-400 rounded-sm opacity-60"></div>
                                    </div>
                                  )}
                                  QR Pass
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* OTP Modal */}
      {otpModal.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-full max-w-md mx-4 bg-white rounded-lg shadow-lg">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h3 className="text-lg font-medium text-gray-900">
                {otpModal.type === 'checkin' ? 'Entry OTP Verification' : 'Exit OTP Verification'}
              </h3>
              <button
                onClick={closeOtpModal}
                className="text-gray-400 hover:text-gray-600"
                disabled={otpModal.isVerifying}
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <form onSubmit={handleOtpSubmit} className="px-6 py-4">
              <div className="mb-4">
                <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full">
                  <Lock className="w-8 h-8 text-blue-600" />
                </div>
                
                <p className="mb-4 text-sm text-center text-gray-600">
                  Enter the {otpModal.type === 'checkin' ? 'entry' : 'exit'} OTP for{' '}
                  <strong>{otpModal.visitor?.visitor_name}</strong>
                </p>
                
                <div className="mb-4">
                  <label className="block mb-2 text-sm font-medium text-gray-700">
                    OTP Code
                  </label>
                  <input
                    type="text"
                    value={otpModal.otp}
                    onChange={(e) => {
                      const value = e.target.value.replace(/\D/g, '').slice(0, 6);
                      setOtpModal(prev => ({ 
                        ...prev, 
                        otp: value,
                        error: ''
                      }));
                    }}
                    placeholder="Enter 6-digit OTP"
                    maxLength="6"
                    className={`w-full px-3 py-2 text-center text-lg font-mono border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      otpModal.error ? 'border-red-500' : 'border-gray-300'
                    }`}
                    disabled={otpModal.isVerifying}
                    autoFocus
                  />
                  {otpModal.error && (
                    <p className="mt-1 text-xs text-red-600">{otpModal.error}</p>
                  )}
                </div>
              </div>
              
              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={closeOtpModal}
                  disabled={otpModal.isVerifying}
                  className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={otpModal.isVerifying || !otpModal.otp.trim()}
                  className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {otpModal.isVerifying ? (
                    <div className="flex items-center justify-center">
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Verifying...
                    </div>
                  ) : (
                    'Verify OTP'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reschedule Modal */}
      {rescheduleModal.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-full max-w-md mx-4 bg-white rounded-lg shadow-lg">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h3 className="text-lg font-medium text-gray-900">
                Reschedule Visit
              </h3>
              <button
                onClick={closeRescheduleModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <form onSubmit={handleRescheduleSubmit} className="px-6 py-4">
              <div className="mb-4">
                <p className="mb-4 text-sm text-gray-600">
                  Reschedule visit for <strong>{rescheduleModal.visitor?.visitor_name}</strong>
                </p>
                
                <div className="mb-4">
                  <label className="block mb-2 text-sm font-medium text-gray-700">
                    New Visiting Date *
                  </label>
                  <input
                    type="date"
                    value={rescheduleModal.newDate}
                    onChange={(e) => setRescheduleModal(prev => ({ 
                      ...prev, 
                      newDate: e.target.value,
                      errors: { ...prev.errors, newDate: '' }
                    }))}
                    min={new Date().toISOString().split('T')[0]} // Today
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                      rescheduleModal.errors.newDate ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {rescheduleModal.errors.newDate && (
                    <p className="mt-1 text-xs text-red-600">{rescheduleModal.errors.newDate}</p>
                  )}
                </div>
                
                <div className="mb-4">
                  <label className="block mb-2 text-sm font-medium text-gray-700">
                    New Visiting Time *
                  </label>
                  <input
                    type="time"
                    value={rescheduleModal.newTime}
                    onChange={(e) => setRescheduleModal(prev => ({ 
                      ...prev, 
                      newTime: e.target.value,
                      errors: { ...prev.errors, newTime: '' }
                    }))}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                      rescheduleModal.errors.newTime ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {rescheduleModal.errors.newTime && (
                    <p className="mt-1 text-xs text-red-600">{rescheduleModal.errors.newTime}</p>
                  )}
                </div>
              </div>
              
              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={closeRescheduleModal}
                  className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loadingActions[`${rescheduleModal.visitor?.id}-reschedule`]}
                  className="flex-1 px-4 py-2 text-sm font-medium text-purple-800 bg-white border border-purple-800 rounded-md hover:bg-purple-100 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loadingActions[`${rescheduleModal.visitor?.id}-reschedule`] ? (
                    <div className="flex items-center justify-center">
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Rescheduling...
                    </div>
                  ) : (
                    'Reschedule'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
    );
  };
  
  export default VisitorTable;