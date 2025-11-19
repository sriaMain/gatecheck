import React from "react";
import { Edit, Eye, EyeOff } from "lucide-react";

const UserRoleTable = ({ userRoles, onEdit, onShowEditModal, onToggleActive }) => {
  return (
    <div className="overflow-x-auto bg-white rounded-lg shadow">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">User</th>
            <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">Role</th>
            <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {userRoles.map((userRole) => {
            // Debug: log userRole object structure
            console.log('UserRoleTable row:', userRole);
            return (
              <tr key={userRole.user_role_id || userRole.id}>
                <td className="px-6 py-4 whitespace-nowrap">{userRole.user_name}</td>
                <td className="px-6 py-4 whitespace-nowrap">{userRole.role_name}</td>
                <td className="px-6 py-4 text-sm whitespace-nowrap">
                  <button
                    onClick={() => {
                      onEdit(userRole);
                      onShowEditModal(true);
                    }}
                    className="text-indigo-600 hover:text-indigo-900"
                  >
                    <Edit size={18} />
                  </button>
                  <button
                    onClick={() => onToggleActive && onToggleActive(userRole)}
                    className={`ml-4 p-1 rounded ${
                      userRole.is_active || userRole.isActive || userRole.active
                        ? 'text-green-600 hover:text-green-900'
                        : 'text-gray-400 hover:text-gray-600'
                    }`}
                    title={userRole.is_active || userRole.isActive || userRole.active ? 'Deactivate' : 'Activate'}
                  >
                    {userRole.is_active || userRole.isActive || userRole.active ? (
                      <EyeOff size={18} />
                    ) : (
                      <Eye size={18} />
                    )}
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default UserRoleTable;
