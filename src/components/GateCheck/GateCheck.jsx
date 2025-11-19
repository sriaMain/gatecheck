import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../Auth/api';
import VisitorTable from './VisitorTable';
import VisitorForm from './VisitorForm';
import Header from './Header';
import SearchBar from './SearchBar';
import { Loader2, AlertCircle, CheckCircle } from 'lucide-react';

const GateCheck = ({ onVisitorCountChange, userCompany, user }) => {
  const [visitors, setVisitors] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [recurringVisitors, setRecurringVisitors] = useState([]);
  const [categories, setCategories] = useState([]);
  const [filteredVisitors, setFilteredVisitors] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [filterCategory, setFilterCategory] = useState('all');
  const [loading, setLoading] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [categoriesLoading, setCategoriesLoading] = useState(false);
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);
  const [showExcelDropdown, setShowExcelDropdown] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showRecurring, setShowRecurring] = useState(false);
  const [errors, setErrors] = useState({});
  const [successMessage, setSuccessMessage] = useState('');
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const [formData, setFormData] = useState({
    visitor_name: '',
    mobile_number: '',
    email_id: '',
    gender: '',
    pass_type: 'ONE_TIME',
    visiting_date: '',
    visiting_time: '',
    recurring_days: '',
    allowing_hours: '8',
    category: '',
    whom_to_meet: '',
    coming_from: '',
    purpose_of_visit: '',
    belongings_tools: '',
    security_notes: '',
    vehicle_type: '',
    vehicle_number: '',
    valid_until: ''
  });

  const applyFilters = useCallback((data) => {
    if (!Array.isArray(data) || data.length === 0) return [];
    let filtered = [...data];

    if (searchTerm && searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase().trim();
      filtered = filtered.filter(visitor =>
        visitor.visitor_name?.toLowerCase().includes(searchLower) ||
        visitor.mobile_number?.includes(searchTerm) ||
        visitor.email_id?.toLowerCase().includes(searchLower) ||
        visitor.coming_from?.toLowerCase().includes(searchLower) ||
        visitor.purpose_of_visit?.toLowerCase().includes(searchLower) ||
        visitor.pass_id?.toLowerCase().includes(searchLower)
      );
    }

    if (filterStatus !== 'all') {
      filtered = filtered.filter(visitor => visitor.status === filterStatus);
    }

    if (filterType !== 'all') {
      filtered = filtered.filter(visitor =>
        (visitor.pass_type && visitor.pass_type.toUpperCase() === filterType.toUpperCase())
      );
    }

    if (filterCategory !== 'all') {
      filtered = filtered.filter(visitor =>
        visitor.category_details?.name === filterCategory ||
        visitor.category === filterCategory
      );
    }
    return filtered;
  }, [searchTerm, filterStatus, filterType, filterCategory]);

  const fetchCategories = useCallback(async () => {
    try {
      setCategoriesLoading(true);
      const response = await api.visitors.category();
      if (response && response.data) {
        const categoriesData = response.data.categories || response.data;
        if (Array.isArray(categoriesData)) {
          setCategories(categoriesData);
        }
      }
    } catch (error) {
      console.error('Error fetching categories:', error);
      setCategories([]);
      setErrors(prev => ({ ...prev, categories: 'Failed to load categories' }));
    } finally {
      setCategoriesLoading(false);
    }
  }, []);

  const fetchVisitors = useCallback(async () => {
    try {
      setLoading(true);
      setErrors(prev => ({ ...prev, general: "" }));
      const companyId = userCompany;
      const visitorsResponse = await api.visitors.getAll({ companyId });
      console.log(visitorsResponse);
      if (visitorsResponse?.data) {
        const visitorsData = visitorsResponse.data.visitors || visitorsResponse.data;
        const visitorsArray = Array.isArray(visitorsData) ? visitorsData : [];
        setVisitors(visitorsArray);
        const filtered = applyFilters(visitorsArray);
        setFilteredVisitors(filtered);
        if (onVisitorCountChange) {
          onVisitorCountChange(visitorsArray.length);
        }
      }
    } catch (error) {
      console.error("Error fetching visitors:", error);
      setErrors(prev => ({ ...prev, general: "Failed to load visitors data. Please try again." }));
      setVisitors([]);
      setFilteredVisitors([]);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, filterStatus, filterType, filterCategory, showRecurring, applyFilters, userCompany, onVisitorCountChange]);

  const autoRefresh = useCallback(async () => {
    try {
      setErrors({});
      await fetchVisitors();
    } catch (error) {
      console.error('Error during auto refresh:', error);
      setErrors(prev => ({ ...prev, general: 'Failed to refresh data. Please try again.' }));
    }
  }, [fetchVisitors]);

  const triggerRefresh = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  useEffect(() => {
    const loadInitialData = async () => {
      await fetchCategories();
      await fetchVisitors();
    };
    loadInitialData();
  }, [showRecurring]);

  useEffect(() => {
    if (refreshTrigger > 0) {
      autoRefresh();
    }
  }, [refreshTrigger, autoRefresh]);

  useEffect(() => {
    if (searchTerm !== '') {
      const timeoutId = setTimeout(() => {
        fetchVisitors();
      }, 500);
      return () => clearTimeout(timeoutId);
    } else if (searchTerm === '') {
      fetchVisitors();
    }
  }, [searchTerm, fetchVisitors]);

  useEffect(() => {
    if (filterStatus !== 'all' || filterType !== 'all' || filterCategory !== 'all') {
      const timeoutId = setTimeout(() => {
        fetchVisitors();
      }, 100);
      return () => clearTimeout(timeoutId);
    }
  }, [filterStatus, filterType, filterCategory, showRecurring, fetchVisitors]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const resetForm = () => {
    setFormData({
      visitor_name: '',
      mobile_number: '',
      email_id: '',
      gender: '',
      pass_type: 'ONE_TIME',
      visiting_date: '',
      visiting_time: '',
      recurring_days: '',
      allowing_hours: '8',
      category: '',
      whom_to_meet: '',
      coming_from: '',
      purpose_of_visit: '',
      belongings_tools: '',
      security_notes: '',
      vehicle_type: '',
      vehicle_number: '',
      valid_until: ''
    });
    setErrors({});
    setSuccessMessage('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validateForm();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setSubmitLoading(true);
    setErrors({});
    setSuccessMessage('');
    try {
      const visitorPayload = {
        visitor_name: formData.visitor_name.trim(),
        mobile_number: formData.mobile_number.trim(),
        email_id: formData.email_id.trim(),
        gender: formData.gender,
        pass_type: formData.pass_type,
        visiting_date: formData.visiting_date,
        visiting_time: formData.visiting_time,
        recurring_days: formData.pass_type === 'RECURRING' ? parseInt(formData.recurring_days) : null,
        allowing_hours: parseInt(formData.allowing_hours),
        category: formData.category.trim(),
        whom_to_meet: formData.whom_to_meet.trim() || '',
        coming_from: formData.coming_from.trim() || '',
        purpose_of_visit: formData.purpose_of_visit.trim(),
        belongings_tools: formData.belongings_tools.trim() || '',
        security_notes: formData.security_notes.trim() || null,
        vehicle_type: formData.vehicle_type || null,
        vehicle_number: formData.vehicle_number.trim() || null,
        valid_until: formData.valid_until || null
      };
      let response;
      if (formData.pass_type === 'RECURRING') {
        response = await api.visitors.create(visitorPayload);
      } else {
        response = await api.visitors.createRecurring(visitorPayload);
      }
      if (response && response.data) {
        setSuccessMessage(`Visitor ${formData.pass_type === 'RECURRING' ? 'recurring pass' : ''} added successfully!`);
        await autoRefresh();
        setTimeout(() => {
          setShowAddModal(false);
          resetForm();
        }, 1000);
      }
    } catch (error) {
      let errorMessage = 'Failed to add visitor. Please try again.';
      if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.response?.data?.errors) {
        const backendErrors = error.response.data.errors;
        if (typeof backendErrors === 'object') {
          const formattedErrors = {};
          for (const [field, messages] of Object.entries(backendErrors)) {
            formattedErrors[field] = Array.isArray(messages) ? messages[0] : messages;
          }
          setErrors(formattedErrors);
          return;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      if (errorMessage.toLowerCase().includes('phone') || errorMessage.toLowerCase().includes('mobile')) {
        setErrors({ mobile_number: errorMessage });
      } else if (errorMessage.toLowerCase().includes('email')) {
        setErrors({ email_id: errorMessage });
      } else if (errorMessage.toLowerCase().includes('duplicate') || errorMessage.toLowerCase().includes('already exists')) {
        setErrors({ mobile_number: 'Visitor with this phone number already exists' });
      } else {
        setErrors({ general: errorMessage });
      }
    } finally {
      setSubmitLoading(false);
    }
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.visitor_name.trim()) newErrors.visitor_name = 'Please enter visitor name';
    if (!formData.mobile_number.trim()) newErrors.mobile_number = 'Please enter mobile number';
    if (!formData.email_id.trim()) newErrors.email_id = 'Please enter email address';
    if (!formData.gender.trim()) newErrors.gender = 'Please select gender';
    if (!formData.pass_type.trim()) newErrors.pass_type = 'Please select pass type';
    if (!formData.visiting_date.trim()) newErrors.visiting_date = 'Please select visiting date';
    if (!formData.visiting_time.trim()) newErrors.visiting_time = 'Please enter visiting time';
    if (!formData.allowing_hours.trim()) newErrors.allowing_hours = 'Please enter allowing hours';
    if (formData.purpose_of_visit.trim() === '') newErrors.purpose_of_visit = 'Please enter purpose of visit';
    if (formData.visiting_date) {
      const selectedDate = new Date(formData.visiting_date);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (selectedDate < today) {
        newErrors.visiting_date = 'Visiting date cannot be in the past';
      }
    }
    if (formData.pass_type === 'RECURRING') {
      if (!formData.recurring_days.trim()) newErrors.recurring_days = 'Please enter number of recurring days';
      if (!formData.valid_until.trim()) newErrors.valid_until = 'Please select valid until date';
    }
    if (!formData.category.trim()) newErrors.category = 'Please select a category';
    return newErrors;
  };

  const handleVisitorUpdate = async (visitorId, newStatus, actionType, additionalData = {}) => {
    try {
      setErrors(prev => ({ ...prev, general: '' }));
      const updateVisitorInState = (visitorId, newStatus, additionalData = {}) => {
        setVisitors(prev => prev.map(visitor =>
          visitor.id === visitorId ? { ...visitor, status: newStatus, ...additionalData } : visitor
        ));
        setRecurringVisitors(prev => prev.map(visitor =>
          visitor.id === visitorId ? { ...visitor, status: newStatus, ...additionalData } : visitor
        ));
      };
      updateVisitorInState(visitorId, newStatus, additionalData);
      const updatePayload = { status: newStatus, action_type: actionType, ...additionalData };
      const response = await api.visitors.updateStatus(visitorId, updatePayload);
      setSuccessMessage(`Visitor status updated to ${newStatus.toLowerCase().replace('_', ' ')}`);
      await autoRefresh();
      setTimeout(() => { setSuccessMessage(''); }, 3000);
    } catch (error) {
      console.error('Error updating visitor:', error);
      const revertVisitorInState = (visitorId) => { fetchVisitors(); };
      revertVisitorInState(visitorId);
      let errorMessage = 'Failed to update visitor status. Please try again.';
      if (error.response) {
        if (error.response.data?.message) errorMessage = error.response.data.message;
        else if (error.response.data?.error) errorMessage = error.response.data.error;
        else if (error.response.data?.errors) errorMessage = Object.values(error.response.data.errors).flat().join(', ');
        if (error.response.status === 404) errorMessage = 'Visitor not found. Please refresh and try again.';
        else if (error.response.status === 403) errorMessage = 'You do not have permission to perform this action.';
        else if (error.response.status === 422) errorMessage = 'Invalid data provided. Please check and try again.';
      } else if (error.request) errorMessage = 'Network error. Please check your connection and try again.';
      setErrors(prev => ({ ...prev, general: errorMessage }));
      setTimeout(() => { triggerRefresh(); }, 2000);
    }
  };

  const handleReschedule = async (visitorId, newVisitingDate, newVisitingTime, additionalData = {}) => {
    try {
      setErrors(prev => ({ ...prev, general: '' }));
      const updateVisitorScheduleInState = (visitorId, newVisitingDate, newVisitingTime, additionalData = {}) => {
        setVisitors(prev => prev.map(visitor =>
          visitor.id === visitorId ? { ...visitor, visiting_date: newVisitingDate, visiting_time: newVisitingTime, ...additionalData } : visitor
        ));
        setRecurringVisitors(prev => prev.map(visitor =>
          visitor.id === visitorId ? { ...visitor, visiting_date: newVisitingDate, visiting_time: newVisitingTime, ...additionalData } : visitor
        ));
      };
      updateVisitorScheduleInState(visitorId, newVisitingDate, newVisitingTime, additionalData);
      const reschedulePayload = { visiting_date: newVisitingDate, visiting_time: newVisitingTime, action_type: 'reschedule', ...additionalData };
      let response;
      if (api.visitors.reschedule) response = await api.visitors.reschedule(visitorId, reschedulePayload);
      else response = await api.visitors.updateStatus(visitorId, reschedulePayload);
      setSuccessMessage(`Visitor rescheduled successfully to ${newVisitingDate} at ${newVisitingTime}`);
      await autoRefresh();
      setTimeout(() => { setSuccessMessage(''); }, 3000);
    } catch (error) {
      console.error('Error rescheduling visitor:', error);
      const revertVisitorInState = (visitorId) => { fetchVisitors(); };
      revertVisitorInState(visitorId);
      let errorMessage = 'Failed to reschedule visitor. Please try again.';
      if (error.response) {
        if (error.response.data?.message) errorMessage = error.response.data.message;
        else if (error.response.data?.error) errorMessage = error.response.data.error;
        else if (error.response.data?.errors) errorMessage = Object.values(error.response.data.errors).flat().join(', ');
        if (error.response.status === 404) errorMessage = 'Visitor not found. Please refresh and try again.';
        else if (error.response.status === 403) errorMessage = 'You do not have permission to reschedule this visitor.';
        else if (error.response.status === 422) errorMessage = 'Invalid date or time provided. Please check and try again.';
        else if (error.response.status === 400) errorMessage = 'Invalid reschedule data. Please check the date and time format.';
      } else if (error.request) errorMessage = 'Network error. Please check your connection and try again.';
      setErrors(prev => ({ ...prev, general: errorMessage }));
      setTimeout(() => { triggerRefresh(); }, 2000);
    }
  };

  const handleFilterStatusChange = (newStatus) => { setFilterStatus(newStatus); };
  const handleFilterTypeChange = (newType) => { setFilterType(newType); };
  const handleFilterCategoryChange = (newCategory) => { setFilterCategory(newCategory); };
  const handleClearFilters = () => { setFilterStatus('all'); setFilterType('all'); setFilterCategory('all'); setSearchTerm(''); };
  const handleRecurringToggle = (newShowRecurring) => { setShowRecurring(newShowRecurring); setFilteredVisitors([]); };
  const handleSearchChange = (newSearchTerm) => { setSearchTerm(newSearchTerm); };
  const handleManualRefresh = async () => { await autoRefresh(); };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center space-x-2">
          <Loader2 className="w-8 h-8 text-purple-800 animate-spin" />
          <span className="text-gray-600">Loading visitors...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen m-0 bg-gray-50">
      {errors.general && (
        <div className="mx-6 mt-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 mr-2 text-red-500" />
              <span className="text-red-700">{errors.general}</span>
            </div>
            <button onClick={handleManualRefresh} className="px-3 py-1 text-xs text-red-600 border border-red-300 rounded hover:bg-red-50">
              Retry
            </button>
          </div>
        </div>
      )}
      {successMessage && (
        <div className="mx-6 mt-4 rounded-lg">
          <div className="flex items-center">
            <CheckCircle className="w-5 h-5 mr-2 text-green-500" />
            <span className="text-green-700">{successMessage}</span>
          </div>
        </div>
      )}
      <Header
        showRecurring={showRecurring}
        setShowRecurring={handleRecurringToggle}
        setShowAddModal={setShowAddModal}
        showFilterDropdown={showFilterDropdown}
        setShowFilterDropdown={setShowFilterDropdown}
        filterStatus={filterStatus}
        setFilterStatus={handleFilterStatusChange}
        filterType={filterType}
        setFilterType={handleFilterTypeChange}
        filterCategory={filterCategory}
        setFilterCategory={handleFilterCategoryChange}
        categories={categories}
        showExcelDropdown={showExcelDropdown}
        setShowExcelDropdown={setShowExcelDropdown}
        onClearFilters={handleClearFilters}
      />
      <SearchBar searchTerm={searchTerm} setSearchTerm={handleSearchChange} />
      <VisitorTable
        filteredVisitors={filteredVisitors}
        showRecurring={showRecurring}
        onVisitorUpdate={handleVisitorUpdate}
        onVisitorReschedule={handleReschedule}
        getStatusColor={(status) => {
          switch(status) {
            case 'APPROVED': return 'text-green-800 bg-green-100';
            case 'PENDING': return 'text-yellow-800 bg-yellow-100';
            case 'REJECTED': return 'text-red-800 bg-red-100';
            case 'EXPIRED': return 'text-gray-800 bg-gray-100';
            case 'CANCELLED': return 'text-orange-800 bg-orange-100';
            case 'BLACKLISTED': return 'text-red-800 bg-red-200';
            case 'CHECKED_IN': return 'text-blue-800 bg-blue-100';
            case 'CHECKED_OUT': return 'text-purple-800 bg-purple-100';
            case 'VISITED': return 'text-green-800 bg-green-100';
            case 'COMPLETED': return 'text-gray-800 bg-gray-100';
            default: return 'text-gray-800 bg-gray-100';
          }
        }}
        getStatusDot={(status) => {
          switch(status) {
            case 'APPROVED': return 'bg-green-500';
            case 'PENDING': return 'bg-yellow-500';
            case 'REJECTED': return 'bg-red-500';
            case 'EXPIRED': return 'bg-gray-500';
            case 'CANCELLED': return 'bg-orange-500';
            case 'BLACKLISTED': return 'bg-red-600';
            case 'CHECKED_IN': return 'bg-blue-500';
            case 'CHECKED_OUT': return 'bg-purple-500';
            case 'VISITED': return 'bg-green-500';
            case 'COMPLETED': return 'bg-gray-500';
            default: return 'bg-gray-500';
          }
        }}
        getPassTypeLabel={(passType) => {
          switch(passType) {
            case 'ONE_TIME': return 'One Time';
            case 'RECURRING': return 'Recurring';
            case 'PERMANENT': return 'Permanent';
            default: return passType;
          }
        }}
        getCategoryLabel={(categoryValue) => {
          const categoryByValue = categories.find(cat => cat.value === categoryValue);
          if (categoryByValue) return categoryByValue.name;
          const categoryByName = categories.find(cat => cat.name === categoryValue);
          if (categoryByName) return categoryByName.name;
          return categoryValue;
        }}
        searchTerm={searchTerm}
        filterStatus={filterStatus}
        filterType={filterType}
        filterCategory={filterCategory}
      />
      {showAddModal && (
        <VisitorForm
          formData={formData}
          handleInputChange={handleInputChange}
          handleSubmit={handleSubmit}
          setShowAddModal={setShowAddModal}
          resetForm={resetForm}
          errors={errors}
          submitLoading={submitLoading}
          categories={categories}
          categoriesLoading={categoriesLoading}
          successMessage={successMessage}
          userCompany={userCompany}
          user={user}
        />
      )}
    </div>
  );
};

export default GateCheck;
