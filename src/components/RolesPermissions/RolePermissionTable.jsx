import React from "react";
import { Edit2, Shield, Key, ToggleLeft, ToggleRight } from "lucide-react";

const RolePermissionTable = ({ rolePermissions, onEdit, onShowEditModal, onToggleActive }) => {

  console.log('RolePermissionTable props:', { rolePermissions });
  const handleEdit = (rolePermission) => {
    
    
    onEdit(rolePermission);
    onShowEditModal(true);
  };

  if (rolePermissions.length === 0) {
    return (
      <div className="p-8 text-center bg-white border rounded-lg shadow-sm">
        <Shield className="mx-auto mb-4 text-gray-400" size={48} />
        <h3 className="mb-2 text-lg font-medium text-gray-900">No role permissions found</h3>
        <p className="text-gray-500">No role permissions have been assigned yet.</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden bg-white border rounded-lg shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                Role
              </th>
              <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                Permissions
              </th>
              <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                Permission Count
              </th>
              <th className="px-6 py-3 text-xs font-medium tracking-wider text-right text-gray-500 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {rolePermissions.map((rolePermission, index) => (
              <tr key={rolePermission.id || index} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <Shield className="w-5 h-5 mr-2 text-purple-600" />
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {rolePermission.role}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-wrap gap-1">
                    {rolePermission.permission.slice(0, 3).map((perm, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-1 text-xs font-medium text-blue-800 bg-blue-100 rounded-full"
                      >
                        <Key className="w-3 h-3 mr-1" />
                        {perm}
                      </span>
                    ))}
                    {rolePermission.permission.length > 3 && (
                      <span className="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-800 bg-gray-100 rounded-full">
                        +{rolePermission.permission.length - 3} more
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {rolePermission.permission.length} permission{rolePermission.permission.length !== 1 ? 's' : ''}
                  </div>
                </td>
                <td className="px-6 py-4 text-sm font-medium text-right whitespace-nowrap">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => handleEdit(rolePermission)}
                      className="p-1 text-gray-400 transition-colors hover:text-purple-600"
                      title="Edit role permissions"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      onClick={() => onToggleActive && onToggleActive(rolePermission)}
                      className={`p-1 transition-colors ${
                        (rolePermission.is_active || rolePermission.isActive || rolePermission.active) ? 'text-green-600 hover:text-green-800' : 'text-gray-400 hover:text-gray-600'
                      }`}
                      title={(rolePermission.is_active || rolePermission.isActive || rolePermission.active) ? 'Deactivate' : 'Activate'}
                    >
                      {(rolePermission.is_active || rolePermission.isActive || rolePermission.active) ? (
                        <ToggleRight size={16} />
                      ) : (
                        <ToggleLeft size={16} />
                      )}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RolePermissionTable;