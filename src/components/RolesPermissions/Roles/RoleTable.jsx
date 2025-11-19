import React from 'react';
import { Edit, Eye, EyeOff, Trash2, Calendar, Users, User } from 'lucide-react';

const RoleTable = ({ roles, onEdit, onShowEditModal, onToggleStatus, onDelete }) => {
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

  return (
    <div className="overflow-x-auto bg-white border rounded-lg shadow-sm">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">Role Name</th>
            <th className="px-4 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">Status</th>
            <th className="px-4 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">Created</th>
            <th className="px-4 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">Modified</th>
            <th className="px-4 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">Created By</th>
            <th className="px-4 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {roles.length === 0 ? (
            <tr>
              <td colSpan="6" className="px-4 py-12 text-center text-gray-500">No roles found</td>
            </tr>
          ) : (
            roles.map((role) => (
              <tr key={role.role_id} className="hover:bg-gray-50">
                <td className="p-2 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="p-2 mr-3 bg-purple-100 rounded-full">
                      <Users className="text-purple-600" size={14} />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-900">{role.name}</div>
                      <div className="text-sm text-gray-500">ID: {role.role_id}</div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    role.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {role.is_active ? (
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
                <td className="px-4 py-4 text-sm text-gray-900 whitespace-nowrap">
                  <div className="flex items-center">
                    <Calendar size={16} className="mr-2 text-gray-400" />
                    {formatDate(role.created_at)}
                  </div>
                </td>
                <td className="px-4 py-4 text-sm text-gray-900 whitespace-nowrap">
                  <div className="flex items-center">
                    <Calendar size={16} className="mr-2 text-gray-400" />
                    {formatDate(role.modified_at)}
                  </div>
                </td>
                <td className="px-4 py-4 text-sm text-gray-900 whitespace-nowrap">
                  <div className="flex items-center">
                    <User size={16} className="mr-2 text-gray-400" />
                    {role.created_by || 'System'}
                  </div>
                </td>
                <td className="px-4 py-4 text-sm font-medium whitespace-nowrap">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => {
                        onEdit(role);
                        onShowEditModal(true);
                      }}
                      className="p-1 text-purple-600 rounded hover:text-purple-900"
                      title="Edit Role"
                    >
                      <Edit size={16} />
                    </button>
                    <button
                      onClick={() => onToggleStatus(role.role_id)}
                      className={`p-1 rounded ${
                        role.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'
                      }`}
                      title={role.is_active ? 'Deactivate' : 'Activate'}
                    >
                      {role.is_active ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default RoleTable;
