import numpy as np

class utilities:
    def euler_rotation(self, phi, theta, psi):
        """
        Euler angles to rotation matrix.
        Input : phi, theta, psi in radians
        Output : rotation matrix
        """
        R_x = np.array([[1, 0, 0],
                        [0, np.cos(phi), -np.sin(phi)],
                        [0, np.sin(phi), np.cos(phi)]])
        R_y = np.array([[np.cos(theta), 0, np.sin(theta)],
                        [0, 1, 0],
                        [-np.sin(theta), 0, np.cos(theta)]])
        R_z = np.array([[np.cos(psi), -np.sin(psi), 0],
                        [np.sin(psi), np.cos(psi), 0],
                        [0, 0, 1]])
        return np.matmul(R_z, np.matmul(R_y, R_x))

    def T_angular_inv(self, phi, theta, psi):
        """
        Transformation matrix of angular velocity from body frame to inertial frame.
        Input : phi, theta in radians
        Output : inverse transformation matrix
        """
        T_matrix = np.array([[1, np.sin(phi) * np.tan(theta), np.cos(phi) * np.tan(theta)],
                             [0, np.cos(phi), -np.sin(phi)],
                             [0, np.sin(phi) / np.cos(theta), np.cos(phi) / np.cos(theta)]])
        return T_matrix

    def T_angular(self, phi, theta, psi):
        """
        Transformation matrix of angular velocity from inertial frame to body frame.
        Input : phi, theta in radians
        Output : transformation matrix
        """
        T_matrix = np.array([[1.0, 0.0, -np.sin(theta)],
                            [0.0, np.cos(phi), np.cos(theta) * np.sin(phi)],
                            [0.0, -np.sin(phi), np.cos(theta) * np.cos(phi)]])
        return T_matrix

    def T_angular_inv_dot(self, phi, theta, phi_dot, theta_dot, psi_dot):
        """
        Derivatives of transformation matrix of angular velocity from body frame to inertial frame w.r.t time.
        Input : phi, theta in radians
        Output : first derivative of inverse transformation matrix
        """
        T_inv_dot = np.array([[0,
                               phi_dot * np.cos(phi) * np.tan(theta) + theta_dot * np.sin(phi) / np.cos(theta)**2,
                               -phi_dot * np.sin(phi) * np.cos(theta) + theta_dot * np.cos(phi) / np.cos(theta)**2],
                              [0,
                               -phi_dot * np.sin(phi),
                               -phi_dot * np.cos(phi)],
                              [0,
                               phi_dot * np.cos(phi) / np.cos(theta) + theta_dot * np.sin(phi) * np.tan(theta) / np.cos(theta),
                               -phi_dot * np.sin(phi) / np.cos(theta) + theta_dot * np.cos(phi) * np.tan(theta) / np.cos(theta)]])
        return T_inv_dot

"""### **Runge-Kutta 4th-Order**

https://lpsa.swarthmore.edu/NumInt/NumIntFourth.html
"""

class Quadrotor:
  def __init__(self, config, initial_state=np.zeros(12)):
    self.config = config
    self.state = initial_state  # x, y, z, phi, theta, psi, u, v, w, p, q, r
    self.utils = utilities()
    self.inertia = np.diag([self.config["Ixx"], self.config["Iyy"], self.config["Izz"]]) # diagonal inertia matrix

  def tau_b(self, input: list):
    """
    Calculate the torque of the quadcopter.
    Input : control input
    Output : torque
    """
    u1, u2, u3, u4 = input
    tau_phi = self.config["l"] * self.config["k"] * (u4 - u2)
    tau_theta = self.config["l"] * self.config["k"] * (u3 - u1)
    tau_psi = self.config["b"] * (-u1 + u2 - u3 + u4)
    return np.array([tau_phi, tau_theta, tau_psi])

  def state_derivative(self, state, control):
    """
    Calculate the derivative of the state of the quadcopter.
    Input : state, control
    Output : derivative of states
    """
    zeta = state[0:3]  # x, y, z
    eta = state[3:6]  # phi, theta, psi
    nu = state[6:9]   # u, v, w
    omega = state[9:12]  # p, q, r

    tau_b = self.tau_b(control)
    G = np.array([0.0, 0.0, self.config["g"]])
    T = self.config["k"] * np.sum(control)
    T_body = np.array([0.0, 0.0, T])

    R = self.utils.euler_rotation(eta[0], eta[1], eta[2])
    T_inv = self.utils.T_angular_inv(eta[0], eta[1])

    zeta_dot = R @ nu
    eta_dot = T_inv @ omega

    omega_dot = self.I_inv @ (- np.cross(omega, np.dot(self.I, omega))) + self.I_inv @ tau_b
    nu_dot = -np.cross(omega, nu) - self.config["g"] * R.T @ np.array([0,0,1]) + T_body / self.config["m"]

    return np.hstack([zeta_dot, eta_dot, nu_dot, omega_dot])

  def update_state(self, control: np.array, dt: float):
    """
    Update the state of the quadcopter using RK4 method.
    Input : control, dt
    Output : states
    """
    k1 = self.state_derivative(self.state, control)
    k2 = self.state_derivative(self.state + 0.5 * dt * k1, control)
    k3 = self.state_derivative(self.state + 0.5 * dt * k2, control)
    k4 = self.state_derivative(self.state + dt * k3, control)
    self.state = self.state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
    # self.state = self.state + dt * k1
    return self.state
  

