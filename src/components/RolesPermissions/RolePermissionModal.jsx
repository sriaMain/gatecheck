import React, { useState, useEffect } from "react";
import { X, Shield, Key, Check, Loader } from "lucide-react";

const RolePermissionModal = ({ 
  isOpen, 
  onClose, 
  title, 
  rolePermission, 
  onChange, 
  onSubmit, 
  submitting, 
  roles, 
  permissions,
  isEdit = false
}) => {
  const [selectAll, setSelectAll] = useState(false);
  const [selectedPermissions, setSelectedPermissions] = useState([]);

  useEffect(() => {
    console.log('Modal opened with rolePermission:', rolePermission);
    console.log('Available permissions:', permissions);
    console.log('Is edit mode:', isEdit);
    
    if (isOpen && rolePermission) {
      let permissionIds = [];
      
      if (rolePermission.permission) {
        if (Array.isArray(rolePermission.permission)) {
          rolePermission.permission.forEach(perm => {
            if (typeof perm === 'number') {
              // Handle numeric IDs
              permissionIds.push(perm);
            } else if (typeof perm === 'string') {
              // Handle string permission names or IDs
              const numericId = parseInt(perm);
              if (!isNaN(numericId)) {
                permissionIds.push(numericId);
              } else {
                const permObj = permissions.find(p => p.name === perm);
                if (permObj) {
                  permissionIds.push(permObj.permission_id);
                }
              }
            } else if (typeof perm === 'object') {
              // Handle permission objects
              const id = perm.permission_id || perm.id;
              if (id) {
                permissionIds.push(id);
              }
              // Also check for name field if no ID is found
              else if (perm.name) {
                const found = permissions.find(p => p.name === perm.name);
                if (found) {
                  permissionIds.push(found.permission_id);
                }
              }
            }
          });
        } else if (typeof rolePermission.permission === 'object' && !Array.isArray(rolePermission.permission)) {
          // Handle case where permission might be an object of key-value pairs
          Object.values(rolePermission.permission).forEach(perm => {
            if (typeof perm === 'number') {
              permissionIds.push(perm);
            } else if (typeof perm === 'object' && (perm.permission_id || perm.id)) {
              permissionIds.push(perm.permission_id || perm.id);
            }
          });
        }
      }
      
      // Remove duplicates and filter out invalid values
      permissionIds = [...new Set(permissionIds)].filter(id => id);
      
      console.log('Final processed permission IDs:', permissionIds);
      setSelectedPermissions(permissionIds);
      
      // Update select all state
      if (permissions.length > 0) {
        setSelectAll(permissionIds.length === permissions.length);
      }
    } else {
      // Reset when modal opens without data
      console.log('Resetting permissions - no rolePermission data');
      setSelectedPermissions([]);
      setSelectAll(false);
    }
  }, [isOpen, rolePermission, permissions, isEdit]);

  useEffect(() => {
    if (permissions.length > 0) {
      setSelectAll(selectedPermissions.length === permissions.length);
    }
  }, [selectedPermissions, permissions]);

  if (!isOpen) return null;

  const handleRoleChange = (roleId) => {
    console.log('Role changed to:', roleId);
    onChange({
      ...(rolePermission || {}),
      role: typeof roleId === 'string' && roleId.trim() !== '' && !isNaN(Number(roleId)) ? Number(roleId) : roleId
    });
  };

  const handlePermissionToggle = (permissionId) => {
    let newPermissions;
    if (selectedPermissions.includes(permissionId)) {
      newPermissions = selectedPermissions.filter(id => id !== permissionId);
    } else {
      newPermissions = [...selectedPermissions, permissionId];
    }
    console.log('Permission toggled:', permissionId);
    console.log('Updated permissions:', newPermissions);
    setSelectedPermissions(newPermissions);
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedPermissions([]);
    } else {
      const allPermissionIds = permissions.map(p => p.permission_id);
      setSelectedPermissions(allPermissionIds);
    }
    setSelectAll(!selectAll);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    console.log('Form submitted with data:');
    console.log('- Role:', rolePermission?.role);
    console.log('- Selected Permissions:', selectedPermissions);

    // Validate before submission
    if (!isEdit && !rolePermission?.role) {
      alert('Please select a role');
      return;
    }

    if (selectedPermissions.length === 0) {
      alert('Please select at least one permission');
      return;
    }

    // Ensure permissions are numeric IDs
    const permissionIds = selectedPermissions.map(id => {
      const num = Number(id);
      return isNaN(num) ? id : num;
    });

    // Determine a safe role id to send to backend (must be the role's id, not the role_permission id)
    const resolveRoleId = (rp) => {
      if (!rp) return null;
      const r = rp.role;
      // If role is an object, try to extract id fields
      if (r && typeof r === 'object') {
        return r.role_id || r.id || null;
      }
      // If role is numeric or numeric-string, prefer that only if it matches a known role
      const num = Number(r);
      if (!isNaN(num) && roles && roles.length > 0) {
        const found = roles.find(role => role.role_id === num || role.id === num);
        if (found) return num;
      }
      // If role is a string name, try to find role by name
      if (typeof r === 'string') {
        const foundByName = (roles || []).find(role => role.name === r || String(role.role_id) === r || String(role.id) === r);
        if (foundByName) return foundByName.role_id || foundByName.id;
      }
      // Fallback: if the modal was given a separate field holding the role id
      if (rp && (rp.role_id || rp.roleId)) return rp.role_id || rp.roleId;
      return null;
    };

    const roleIdForPayload = resolveRoleId(rolePermission) ?? rolePermission?.role ?? '';

    const submissionData = {
      ...(rolePermission || {}),
      // Ensure we send the role's id to the backend
      role: roleIdForPayload,
      permission: permissionIds, // Ensure this is always an array of numeric IDs where possible
      role_permission_id: rolePermission?.role_permission_id || rolePermission?.id
    };

    console.log('Final submission data:', submissionData);

    // Update parent state with current selections
    onChange(submissionData);

    try {
      // Call parent handler with prepared payload and await its completion
      await onSubmit(submissionData);
      // Close the modal after successful submission
      onClose();
    } catch (error) {
      console.error('Error submitting form:', error);
      // Keep the modal open if there's an error
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col h-full">
          <div className="flex-1 px-6 py-4 overflow-y-auto">
            <div className="space-y-4">
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-700">
                  <Shield className="inline w-4 h-4 mr-1" />
                  Role
                </label>
                {isEdit ? (
                  <div className="w-full p-2 text-gray-700 bg-gray-100 border border-gray-300 rounded-lg">
                    {roles.find(r => r.role_id === rolePermission.role)?.name || 'Unknown Role'}
                  </div>
                ) : (
                  <select
                    value={rolePermission.role}
                    onChange={(e) => handleRoleChange(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    required
                  >
                    <option value="">Select a role</option>
                    {roles.map(role => (
                      <option key={role.role_id} value={role.role_id}>
                        {role.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    <Key className="inline w-4 h-4 mr-1" />
                    Permissions
                  </label>
                  <button
                    type="button"
                    onClick={handleSelectAll}
                    className="text-sm text-purple-600 hover:text-purple-800"
                  >
                    {selectAll ? 'Deselect All' : 'Select All'}
                  </button>
                </div>
                
                <div className="p-3 space-y-2 overflow-y-auto border border-gray-200 rounded-lg max-h-64">
                  {permissions.map(permission => (
                    <label
                      key={permission.permission_id}
                      className="flex items-center p-2 space-x-2 rounded cursor-pointer hover:bg-gray-50"
                    >
                      <input
                        type="checkbox"
                        checked={selectedPermissions.includes(permission.permission_id)}
                        onChange={() => handlePermissionToggle(permission.permission_id)}
                        className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                      />
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-900">
                          {permission.name}
                        </div>
                        {permission.description && (
                          <div className="text-xs text-gray-500">
                            {permission.description}
                          </div>
                        )}
                      </div>
                      {selectedPermissions.includes(permission.permission_id) && (
                        <Check className="w-4 h-4 text-green-600" />
                      )}
                    </label>
                  ))}
                </div>
                
                <p className="mt-2 text-xs text-gray-500">
                  {selectedPermissions.length} of {permissions.length} permissions selected
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t bg-gray-50">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center gap-2 px-4 py-2 text-purple-800 bg-transparent border border-purple-800 rounded-lg hover:bg-purple-100 disabled:opacity-50"
            >
              {submitting && <Loader className="w-4 h-4 animate-spin" />}
              {isEdit ? 'Update' : 'Assign'} Permissions
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RolePermissionModal;