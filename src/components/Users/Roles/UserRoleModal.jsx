import React from "react";
import { X } from "lucide-react";

const UserRoleModal = ({ isOpen, onClose, title, userRole, onChange, onSubmit, submitting, users, roles, isEdit }) => {
  if (!isOpen) return null;

 

  return (
    <div className="fixed inset-0 z-50 overflow-auto bg-black bg-opacity-50">
      <div className="relative max-w-md p-8 mx-auto mt-20 bg-white rounded-lg shadow-lg">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-semibold text-gray-900">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <X size={24} />
          </button>
        </div>
        <form onSubmit={(e) => { e.preventDefault(); onSubmit(); }} className="mt-4">
          <div className="mb-4">
            <label htmlFor="user" className="block text-sm font-medium text-gray-700">User</label>
            <select
              id="user"
              value={userRole.user}
              onChange={(e) => onChange({ ...userRole, user: e.target.value })}
              className="block w-full p-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Select a user</option>
              {users.map((user) => (
                <option key={user.id} value={user.id}>{user.username}</option>
              ))}
            </select>
          </div>
          <div className="mb-4">
            <label htmlFor="role" className="block text-sm font-medium text-gray-700">Role</label>
            <select
              id="role"
              
              value={userRole.role}
              onChange={(e) => onChange({ ...userRole, role: e.target.value }
               
              ) }
              className="block w-full p-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Select a role</option>
              {roles.map((role) => (
                <option key={role.
                  role_id} value={role.
                  role_id
                  }>{role.name}</option>
              ))}
            </select>
          </div>
          <div className="mb-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={!!userRole.is_active}
                onChange={e => onChange({ ...userRole, is_active: e.target.checked })}
                className="mr-2"
              />
              <span className="text-sm font-medium text-gray-700">Active</span>
            </label>
          </div>
          <div className="flex justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex justify-center px-4 py-2 ml-3 text-sm font-medium text-purple-600 bg-transparent border border-purple-800 rounded-md shadow-sm hover:bg-purple-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {submitting ? 'Submitting...' : isEdit ? 'Update' : 'Submit'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UserRoleModal;
