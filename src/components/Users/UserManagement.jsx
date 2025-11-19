import React, { useState, useEffect } from 'react';
import { FaBuilding, FaUsers, FaCalendar, FaArrowLeft, FaPlus, FaExclamationTriangle, FaSearch } from 'react-icons/fa';
import { Loader2 } from 'lucide-react';
import { api } from '../Auth/api';
import { useNavigate, useLocation } from 'react-router-dom';
import AddUserModal from './AddUserModal';
import UserList from './UserList';
import UserModals from './UserModals';


const UserManagement = ({ onBack, onUpdateOrganization, onNavigateToOrganizations, onUserCountChange }) => {
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers]= useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [deleteLoading, setDeleteLoading] = useState({});
  const [updateLoading, setUpdateLoading] = useState({});
  const [userDetailsLoading, setUserDetailsLoading] = useState({});
  const [showEditModal, setShowEditModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [editFormData, setEditFormData] = useState({});
  const navigate = useNavigate();
  const location = useLocation();
  const organization = location.state?.organization;

  useEffect(() => {
    if (organization?.id) {
      console.log('Organization changed, loading users for:', organization.id);
      loadUsers();
    } else {
      console.log('No organization ID, using fallback users');
      setUsers(organization?.users || []);
      setFilteredUsers(organization?.users || []);
    }
  }, [organization?.id]);

  useEffect(() => {
    if (onUserCountChange && typeof onUserCountChange === 'function') {
      onUserCountChange(users.length);
    }
  }, [users.length, onUserCountChange]);

  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredUsers(users);
    } else {
      const filtered = users.filter(user => {
        const userName = (user.username || user.name || '').toLowerCase();
        const userEmail = (user.email || '').toLowerCase(); 
        const searchLower = searchTerm.toLowerCase();

        return userName.includes(searchLower) || userEmail.includes(searchLower);
      });
      setFilteredUsers(filtered);
    }
  }, [searchTerm, users]);

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };
  const clearSearch = () => {
    setSearchTerm('');
  };

  const loadUsers = async () => {
    if (!organization?.id) {
      console.log('No organization ID provided');
      return;
    }
    setLoading(true);
    setErrors({});
    try {
      console.log('Loading users for organization:', organization.id);
      const response = await api.user.getByOrganization(organization.id);
      console.log('API Response:', response);
      if (response.data) {
        const fetchedUsers = Array.isArray(response.data) ? response.data : response.data.users || [];
        console.log('Users loaded successfully:', fetchedUsers.length);
        setUsers(fetchedUsers);
        setFilteredUsers(fetchedUsers);
        if (onUserCountChange) {
          onUserCountChange(fetchedUsers.length);
        }
      } else {
        console.log('No data in response, setting empty users array');
        setUsers([]);
        setFilteredUsers([]);
        if (onUserCountChange) {
          onUserCountChange(0);
        }
      }
    } catch (error) {
      console.error('Error loading users:', error);
      let errorMessage = 'Failed to load users. Please try again.';
      if (error.response?.status === 404) {
        errorMessage = 'No users found for this organization.';
      } else if (error.response?.status === 403) {
        errorMessage = 'You do not have permission to view users for this organization.';
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      if (error.code === 'NETWORK_ERROR' || !navigator.onLine) {
        errorMessage = 'Network error. Please check your connection and try again.';
      }
      setErrors({ load: errorMessage });
      if (organization?.users) {
        console.log('Using fallback users from organization object');
        setUsers(organization.users);
        setFilteredUsers(organization.users);
        if (onUserCountChange) {
          onUserCountChange(organization.users.length);
        }
      } else {
        setUsers([]);
        if (onUserCountChange) {
          onUserCountChange(0);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const handleViewUserDetails = async (user) => {
    setSelectedUser(user);
    setShowViewModal(true);
    try {
      const userDetails = await api.organization.getUsers(user.id);
      if (userDetails) {
        setSelectedUser(userDetails);
      }
    } catch (error) {
      console.log('Failed to load detailed user information');
    }
  };

  const handleEditUser = (user) => {
    setSelectedUser(user);
    setEditFormData({
      username: user.username || user.name || '',
      email: user.email || '',
      block: user.block || '',
      floor: user.floor || '',
      // prefer explicit boolean is_active from backend; fallback to status string
      is_active: (user.is_active === true) ? true : (user.is_active === false ? false : (user.status ? user.status.toLowerCase() === 'active' : true))
    });
    setShowEditModal(true);
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === 'checkbox' ? checked : value;
    setEditFormData(prev => ({
      ...prev,
      [name]: newValue
    }));
  };

  const handleSaveUser = async () => {
    if (!selectedUser) return;
    setUpdateLoading(prev => ({ ...prev, [selectedUser.id]: true }));
    setErrors({});
    try {
      console.log('Updating user:', selectedUser.id, editFormData);
      // send is_active boolean to backend (ensure compatibility with older status field)
      const payload = { ...editFormData };
      // if payload contains status string, remove it in favor of is_active
      if (payload.status !== undefined && payload.is_active === undefined) {
        payload.is_active = payload.status === 'active';
        delete payload.status;
      }
      const response = await api.organization.updateUser(selectedUser.id, payload);
      const updatedUser = response.data;
      console.log('User updated successfully:', updatedUser);
      const updatedUsers = users.map(user =>
        user.id === selectedUser.id ? { ...user, ...updatedUser, ...editFormData } : user
      );
      setUsers(updatedUsers);
      if (onUpdateOrganization) {
        const updatedOrganization = {
          ...organization,
          users: updatedUsers
        };
        onUpdateOrganization(updatedOrganization);
      }
      setShowEditModal(false);
      setSelectedUser(null);
      setEditFormData({});
      console.log('User updated successfully');
    } catch (error) {
      console.error('Error updating user:', error);
      let errorMessage = 'Failed to update user. Please try again.';
      if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      if (error.code === 'NETWORK_ERROR' || !navigator.onLine) {
        errorMessage = 'Network error. Please check your connection and try again.';
      }
      setErrors({ update: errorMessage });
    } finally {
      setUpdateLoading(prev => ({ ...prev, [selectedUser.id]: false }));
    }
  };

  const handleDeleteUserConfirm = (user) => {
    setSelectedUser(user);
    setShowDeleteModal(true);
  };

  const handleDeleteUser = async () => {
    if (!selectedUser) return;
    setDeleteLoading(prev => ({ ...prev, [selectedUser.id]: true }));
    setErrors({});
    try {
      console.log('Deleting user:', selectedUser.id);
      await api.organization.deleteUser(selectedUser.id);
      const updatedUsers = users.filter(user => user.id !== selectedUser.id);
      setUsers(updatedUsers);
      if (onUserCountChange) {
        onUserCountChange(updatedUsers.length);
      }
      if (onUpdateOrganization) {
        const updatedOrganization = {
          ...organization,
          users: updatedUsers
        };
        onUpdateOrganization(updatedOrganization);
      }
      setShowDeleteModal(false);
      setSelectedUser(null);
      console.log('User deleted successfully');
    } catch (error) {
      console.error('Error deleting user:', error);
      let errorMessage = 'Failed to delete user. Please try again.';
      if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      if (error.code === 'NETWORK_ERROR' || !navigator.onLine) {
        errorMessage = 'Network error. Please check your connection and try again.';
      }
      setErrors({ delete: errorMessage });
    } finally {
      setDeleteLoading(prev => ({ ...prev, [selectedUser.id]: false }));
    }
  };

  const handleNavigateToOrganizations = () => {
    if (onNavigateToOrganizations) {
      onNavigateToOrganizations();
    } else if (onBack) {
      onBack();
    } else {
      navigate('/organization');
    }
  };

  const closeModals = () => {
    setShowEditModal(false);
    setShowViewModal(false);
    setShowDeleteModal(false);
    setShowAddUserModal(false);
    setSelectedUser(null);
    setEditFormData({});
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch (error) {
      return 'Invalid Date';
    }
  };

  const getUserStatusColor = (statusOrFlag) => {
    // Accept either a status string ('active','inactive','pending') or a boolean flag
    const status = (typeof statusOrFlag === 'boolean')
      ? (statusOrFlag ? 'active' : 'inactive')
      : (typeof statusOrFlag === 'string' ? statusOrFlag : (statusOrFlag?.status || ''));
    switch ((status || '').toLowerCase()) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getUserCountSummary = () => {
    const activeUsers = users.filter(user => (user.is_active === true) || (user.status && String(user.status).toLowerCase() === 'active')).length;
    const inactiveUsers = users.filter(user => (user.is_active === false) || (user.status && String(user.status).toLowerCase() === 'inactive')).length;
    const pendingUsers = users.filter(user => user.status && String(user.status).toLowerCase() === 'pending').length;
    return {
      total: users.length,
      active: activeUsers,
      inactive: inactiveUsers,
      pending: pendingUsers
    };
  };

  const userCountSummary = getUserCountSummary();

  if (!organization) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="w-full min-h-screen">
          <main className="p-6">
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <button
                    onClick={handleNavigateToOrganizations}
                    className="flex items-center px-4 py-2 space-x-2 text-purple-800 transition-colors rounded-lg hover:bg-gray-100"
                  >
                    <FaArrowLeft className="w-4 h-4" />
                    <span>Go to Organizations</span>
                  </button>
                  <div className="w-px h-8 bg-gray-300"></div>
                  <div className="flex items-center space-x-3">
                    <FaUsers className="w-6 h-6 text-purple-800" />
                    <div>
                      <h1 className="text-2xl font-bold text-gray-800">User Management</h1>
                      <p className="text-gray-600">No organization selected</p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="py-20 text-center bg-white shadow-sm rounded-xl">
                <div className="flex items-center justify-center w-20 h-20 mx-auto mb-6 bg-purple-100 rounded-full">
                  <FaExclamationTriangle className="w-10 h-10 text-purple-300" />
                </div>
                <h2 className="mb-4 text-2xl font-bold text-gray-800">No Organization Found</h2>
                <p className="max-w-md mx-auto mb-2 text-gray-600">
                  You need to add or select an organization before you can manage users.
                </p>
                <p className="max-w-md mx-auto mb-8 text-sm text-gray-500">
                  Organizations help you group and manage users effectively. Please create an organization first to get started.
                </p>
                <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
                  <button
                    onClick={handleNavigateToOrganizations}
                    className="flex items-center px-8 py-3 space-x-2 text-purple-800 transition-colors bg-transparent border border-purple-800 rounded-lg hover:bg-purple-100 focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                  >
                    <FaBuilding className="w-4 h-4" />
                    <span>Go to Organizations</span>
                  </button>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  }

  const currentOrg = organization;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="w-full min-h-screen">
        <main className="p-6">
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <button
                  onClick={handleNavigateToOrganizations}
                  className="flex items-center px-4 py-2 space-x-2 text-purple-800 transition-colors rounded-lg hover:bg-gray-100"
                >
                  <FaArrowLeft className="w-4 h-4" />
                  <span>Back to Organizations</span>
                </button>
                <div className="w-px h-8 bg-gray-300"></div>
                <div className="flex items-center space-x-3">
                  <FaUsers className="w-6 h-6 text-purple-500" />
                  <div>
                    <h1 className="text-2xl font-bold text-gray-800">User Management</h1>
                    <p className="text-gray-600">
                      {currentOrg.company_name || currentOrg.name} - {users.length} user{users.length !== 1 ? 's' : ''}
                    </p>
                  </div>
                </div>
              </div>
              <button
                onClick={() => setShowAddUserModal(true)}
                className="flex items-center px-4 py-2 space-x-2 text-purple-800 transition-colors bg-transparent border border-purple-800 rounded-lg hover:bg-purple-100"
              >
                <FaPlus className="w-4 h-4" />
                <span>Add User</span>
              </button>
            </div>
            {errors.load && (
              <div className="text-sm text-red-700 rounded-lg">
                <div className="flex items-center space-x-2">
                  <FaExclamationTriangle className="w-4 h-4" />
                  <span>{errors.load}</span>
                </div>
                <button
                  onClick={loadUsers}
                  className="mt-2 text-sm text-red-600 underline hover:text-red-800"
                >
                  Try again
                </button>
              </div>
            )}
            {errors.delete && (
              <div className="text-sm text-red-700 rounded-lg">
                <div className="flex items-center space-x-2">
                  <FaExclamationTriangle className="w-4 h-4" />
                  <span>{errors.delete}</span>
                </div>
              </div>
            )}
            {errors.update && (
              <div className="text-sm text-red-700 rounded-lg">
                <div className="flex items-center space-x-2">
                  <FaExclamationTriangle className="w-4 h-4" />
                  <span>{errors.update}</span>
                </div>
              </div>
            )}
            {Object.keys(errors).filter(key => key.startsWith('user_')).map(errorKey => (
              <div key={errorKey} className="text-sm text-red-700 rounded-lg">
                <div className="flex items-center space-x-2">
                  <FaExclamationTriangle className="w-4 h-4" />
                  <span>{errors[errorKey]}</span>
                </div>
              </div>
            ))}
            <div className="bg-white shadow-sm rounded-xl">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-lg">
                    <FaBuilding className="w-6 h-6 text-purple-500" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-800">{currentOrg.company_name || currentOrg.name}</h2>
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-purple-600">{userCountSummary.total}</div>
                  <div className="text-sm text-gray-500">Total Users</div>
                  <div className="mt-2 text-xs text-gray-400">
                    {userCountSummary.active} Active | {userCountSummary.inactive} Inactive | {userCountSummary.pending} Pending
                  </div>
                </div>
              </div>
            </div>
            <div className="overflow-hidden bg-white shadow-sm rounded-xl">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800">Users</h3>
                    <p className="text-sm text-gray-600">
                      Manage and view all users in this organization ({filteredUsers.length} {searchTerm ? 'filtered' : 'total'})
                    </p>
                  </div>
                 
                
                  {loading && (
                    <div className="flex items-center space-x-2 text-purple-600">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="text-sm">Loading users...</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="realtive">
                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                  <FaSearch className="w-4 h-4 text-gray-400" />
                </div>
                <input
                  type="text"
                  placeholder="Search by name or email..."
                  value={searchTerm}
                  onChange={handleSearchChange}
                  className="  p-2 m-5 text-sm border border-gray-300 rounded-lg  focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  />
                {searchTerm && (
                  <button
                    onClick={clearSearch}
                    className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
                   
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/>
                      </svg>
                    </button>
                )}
                
              </div>
           
              {loading && users.length === 0 ? (
                <div className="py-20 text-center">
                  <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-purple-100 rounded-full">
                    <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
                  </div>
                  <h3 className="mb-2 text-lg font-semibold text-gray-800">Loading Users</h3>
                  <p className="text-gray-600">Please wait while we fetch the user data...</p>
                </div>
              ) : filteredUsers.length === 0 ? (
                <div className="py-20 text-center">
                  <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-purple-100 rounded-full">
                    <FaUsers className="w-8 h-8 text-purple-300" />
                  </div>
                  <h3 className="mb-2 text-lg font-semibold text-gray-800">{searchTerm ? 'No Users Found': 'No Users Yet'}</h3>
                  <p className="mb-6 text-gray-600">
                    {searchTerm ? `No users match your search "${searchTerm}". Try a different search term.`
                      : 'Users will appear here once they are added to this organization.'
                      }
                  </p>
                     {searchTerm && (
                    <button
                      onClick={clearSearch}
                      className="px-4 py-2 text-sm text-purple-600 border border-purple-600 rounded-lg hover:bg-purple-50"
                    >
                      Clear Search
                    </button>
                  )}
                </div>
              ) : (
                <UserList
                  users={filteredUsers}
                  onViewUser={handleViewUserDetails}
                  onEditUser={handleEditUser}
                  onDeleteUser={handleDeleteUserConfirm}
                  loading={loading}
                  deleteLoading={deleteLoading}
                  updateLoading={updateLoading}
                  userDetailsLoading={userDetailsLoading}
                  formatDate={formatDate}
                  getUserStatusColor={getUserStatusColor}
                />
              )}
            </div>
          </div>
        </main>
      </div>
      {showAddUserModal && (
        <AddUserModal
          isOpen={showAddUserModal}
          onClose={closeModals}
          organization={organization}
          onUserAdded={(newUser) => {
            setUsers(prevUsers => [...prevUsers, newUser]);
            if (onUserCountChange) {
              onUserCountChange(users.length + 1);
            }
          }}
        />
      )}
      <UserModals
        showViewModal={showViewModal}
        showEditModal={showEditModal}
        showDeleteModal={showDeleteModal}
        selectedUser={selectedUser}
        editFormData={editFormData}
        onClose={closeModals}
        onInputChange={handleInputChange}
        onSaveUser={handleSaveUser}
        onDeleteUser={handleDeleteUser}
        updateLoading={updateLoading}
        deleteLoading={deleteLoading}
        getUserStatusColor={getUserStatusColor}
        formatDate={formatDate}
      />
    </div>
  );
};

export default UserManagement;


