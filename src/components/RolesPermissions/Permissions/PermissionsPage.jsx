import React, { useState, useEffect } from "react";
import {
  Plus,
  Edit,
  // Trash2,
  Search,
  Shield,
  Eye,
  EyeOff,
  Calendar,
  User,
  Save,
  X,
  AlertCircle,
  CheckCircle,
  Loader,
  RefreshCw
} from "lucide-react";
import { api } from '../../Auth/api';

const PermissionsPage = () => {
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedPermission, setSelectedPermission] = useState(null);
  const [filterActive, setFilterActive] = useState("all");
  const [submitting, setSubmitting] = useState(false);
  const [newPermission, setNewPermission] = useState({
    name: "",
    is_active: true
  });

  useEffect(() => {
    fetchPermissions();
  }, []);

  const fetchPermissions = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.permissions.getAll();
      setPermissions(response.data);
      console.log('Permissions fetched:', response.data); 
    } catch (err) {
      console.error('Error fetching permissions:', err);
      setError('Failed to load permissions. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const filteredPermissions = permissions.filter(permission => {
    const matchesSearch = permission.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterActive === "all" ||
                         (filterActive === "active" && permission.is_active) ||
                         (filterActive === "inactive" && !permission.is_active);
    return matchesSearch && matchesFilter;
  });
  console.log(filteredPermissions);
  const handleAddPermission = async () => {
    if (!newPermission.name.trim()) {
      alert('Please enter a permission name');
      return;
    }
    try {
      setSubmitting(true);
      const response = await api.permissions.create(newPermission);
      setPermissions([...permissions, response.data]);
      setNewPermission({ name: "", is_active: true });
      setShowAddModal(false);
      setError(null);
    } catch (err) {
      console.error('Error creating permission:', err);
      setError(err.response?.data?.message || 'Failed to create permission');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditPermission = async () => {
    if (!selectedPermission || !selectedPermission.name.trim()) {
      alert('Please enter a permission name');
      return;
    }
    try {
      setSubmitting(true);
      const response = await api.permissions.update(selectedPermission.permission_id, selectedPermission);
      console.log(response.data);
      setPermissions(permissions.map(permission =>
        permission.permission_id === selectedPermission.permission_id ? response.data : permission
      ));
      setShowEditModal(false);
      setSelectedPermission(null);
      setError(null);
    } catch (err) {
      console.error('Error updating permission:', err);
      setError(err.response?.data?.message || 'Failed to update permission');
    } finally {
      setSubmitting(false);
    }
  };

  // Delete functionality removed as per requirements

  const togglePermissionStatus = async (permissionId) => {
    const permission = permissions.find(p => p.permission_id === permissionId);
    if (!permission) return;
    try {
      const updatedPermission = { ...permission, is_active: !permission.is_active };
      const response = await api.permissions.update(permissionId, updatedPermission);
      setPermissions(permissions.map(p =>
        p.permission_id === permissionId ? response.data : p
      ));
      setError(null);
    } catch (err) {
      console.error('Error updating permission status:', err);
      setError(err.response?.data?.message || 'Failed to update permission status');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const Modal = ({ isOpen, onClose, title, children }) => {
    if (!isOpen) return null;

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="w-full max-w-md p-6 mx-4 bg-white rounded-lg">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-800">{title}</h2>
            <button
              onClick={onClose}
              className="text-2xl text-gray-500 hover:text-gray-700"
            >
              <X size={24} />
            </button>
          </div>
          {children}
        </div>
      </div>
    );
  };

  const AlertMessage = ({ message, type = 'error' }) => {
    if (!message) return null;

    return (
      <div className={`p-4 rounded-lg mb-4 flex items-center gap-2 ${
        type === 'error' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
      }`}>
        {type === 'error' ? <AlertCircle size={20} /> : <CheckCircle size={20} />}
        <span>{message}</span>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen p-6 bg-gray-50">
        <div className="text-center">
          <Loader className="mx-auto mb-4 text-purple-600 animate-spin" size={48} />
          <p className="text-gray-600">Loading permissions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 bg-gray-50">
      <div className="mx-auto max-w-7xl">
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="flex items-center gap-2 text-3xl font-bold text-gray-900">
                <Shield className="text-purple-600" size={32} />
                Permissions Management
              </h1>
              <p className="mt-1 text-gray-600">Manage user permissions</p>
            </div>
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 px-4 py-2 text-purple-800 transition-colors bg-transparent border border-purple-800 rounded-lg hover:bg-purple-100"
            >
              <Plus size={20} />
              Add Permission
            </button>
          </div>
        </div>

        <AlertMessage message={error} type="error" />

        <div className="grid grid-cols-1 gap-4 mb-6 md:grid-cols-6">
          <div className="p-4 bg-white border rounded-lg shadow-sm h-30">
            <div className="flex items-center">
              <div className="p-3 bg-purple-100 rounded-full">
                <Shield className="text-purple-600" size={24} />
              </div>
              <div className="ml-2">
                <p className="text-xs text-gray-600">Total Permissions</p>
                <p className="text-2xl font-bold text-gray-900">{permissions.length}</p>
              </div>
            </div>
          </div>
          <div className="p-4 bg-white border rounded-lg shadow-sm h-30">
            <div className="flex items-center">
              <div className="p-3 bg-green-100 rounded-full">
                <Eye className="text-green-600" size={24} />
              </div>
              <div className="ml-2">
                <p className="text-xs text-gray-600">Active Permissions</p>
                <p className="text-2xl font-bold text-gray-900">{permissions.filter(p => p.is_active).length}</p>
              </div>
            </div>
          </div>
          <div className="p-4 bg-white border rounded-lg shadow-sm h-30">
            <div className="flex items-center">
              <div className="p-3 bg-red-100 rounded-full">
                <EyeOff className="text-red-600" size={24} />
              </div>
              <div className="ml-2">
                <p className="text-xs text-gray-600">Inactive Permissions</p>
                <p className="text-2xl font-bold text-gray-900">{permissions.filter(p => !p.is_active).length}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="h-20 p-4 mb-6 bg-white border rounded-lg shadow-sm">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <div className="flex items-center gap-4">
              <div className="relative">
                <Search className="absolute text-gray-400 transform -translate-y-1/2 left-3 top-1/2" size={20} />
                <input
                  type="text"
                  placeholder="Search permissions..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="py-2 pl-10 pr-4 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              <select
                value={filterActive}
                onChange={(e) => setFilterActive(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="all">All Permissions</option>
                <option value="active">Active Only</option>
                <option value="inactive">Inactive Only</option>
              </select>
            </div>
            <button
              onClick={fetchPermissions}
              className="flex items-center px-3 py-2 text-purple-600 rounded-lg bg-purple-50 hover:bg-purple-100 disabled:opacity-50"
            >
              <RefreshCw className='w-4 h-4 mr-2' />
              Refresh
            </button>
          </div>
        </div>

        <div className="overflow-hidden bg-white border rounded-lg shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">Permission Name</th>
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">Created</th>
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">Modified</th>
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">Created By</th>
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredPermissions.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center text-gray-500">No permissions found</td>
                  </tr>
                ) : (
                  filteredPermissions.map((permission) => (
                    <tr key={permission.permission_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="p-2 mr-3 bg-purple-100 rounded-full">
                            <Shield className="text-purple-600" size={16} />
                          </div>
                          <div>
                            <div className="text-sm font-medium text-gray-900">{permission.name}</div>
                            <div className="text-sm text-gray-500">ID: {permission.permission_id}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          permission.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {permission.is_active ? (
                            <>
                              <Eye size={12} className="mr-1" />
                              Active
                            </>
                          ) : (
                            <>
                              <EyeOff size={12} className="mr-1" />
                              Inactive
                            </>
                          )}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 whitespace-nowrap">
                        <div className="flex items-center">
                          <Calendar size={16} className="mr-2 text-gray-400" />
                          {formatDate(permission.created_at)}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 whitespace-nowrap">
                        <div className="flex items-center">
                          <Calendar size={16} className="mr-2 text-gray-400" />
                          {formatDate(permission.modified_at)}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 whitespace-nowrap">
                        <div className="flex items-center">
                          <User size={16} className="mr-2 text-gray-400" />
                          {permission.created_by}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm font-medium whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => {
                              setSelectedPermission(permission);
                              setShowEditModal(true);
                            }}
                            className="p-1 text-purple-600 rounded hover:text-purple-900"
                            title="Edit Permission"
                          >
                            <Edit size={16} />
                          </button>
                          <button
                            onClick={() => togglePermissionStatus(permission.permission_id)}
                            className={`p-1 rounded ${
                              permission.is_active
                                ? 'text-red-600 hover:text-red-900'
                                : 'text-green-600 hover:text-green-900'
                            }`}
                            title={permission.is_active ? 'Deactivate' : 'Activate'}
                          >
                            {permission.is_active ? <EyeOff size={16} /> : <Eye size={16} />}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <Modal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          title="Add New Permission"
        >
          <div className="space-y-4">
            <div>
              <label className="block mb-1 text-sm font-medium text-gray-700">
                Permission Name
              </label>
              <input
                type="text"
                value={newPermission.name}
                onChange={(e) => setNewPermission({ ...newPermission, name: e.target.value })}
                placeholder="Enter permission name"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={newPermission.is_active}
                  onChange={(e) => setNewPermission({ ...newPermission, is_active: e.target.checked })}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Active</span>
              </label>
            </div>
            <div className="flex justify-end pt-4 space-x-3">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={handleAddPermission}
                disabled={submitting}
                className="flex items-center gap-2 px-4 py-2 text-purple-800 bg-transparent border border-purple-800 rounded-lg hover:bg-purple-100 disabled:opacity-50"
              >
                {submitting ? <Loader className="animate-spin" size={16} /> : <Save size={16} />}
                {submitting ? 'Adding...' : 'Add Permission'}
              </button>
            </div>
          </div>
        </Modal>

        <Modal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          title="Edit Permission"
        >
          {selectedPermission && (
            <div className="space-y-4">
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-700">
                  Permission Name
                </label>
                <input
                  type="text"
                  value={selectedPermission.name}
                  onChange={(e) => setSelectedPermission({ ...selectedPermission, name: e.target.value })}
                  placeholder="Enter permission name"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedPermission.is_active}
                    onChange={(e) => setSelectedPermission({ ...selectedPermission, is_active: e.target.checked })}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">Active</span>
                </label>
              </div>
              <div className="flex justify-end pt-4 space-x-3">
                <button
                  onClick={() => setShowEditModal(false)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={handleEditPermission}
                  disabled={submitting}
                  className="flex items-center gap-2 px-4 py-2 text-purple-800 bg-transparent border border-purple-800 rounded-lg hover:bg-purple-100 disabled:opacity-50"
                >
                  {submitting ? <Loader className="animate-spin" size={16} /> : <Save size={16} />}
                  {submitting ? 'Updating...' : 'Update Permission'}
                </button>
              </div>
            </div>
          )}
        </Modal>
      </div>
    </div>
  );
};

export default PermissionsPage;
