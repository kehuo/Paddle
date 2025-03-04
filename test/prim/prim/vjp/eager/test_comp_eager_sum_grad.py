# Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

import numpy as np

import paddle
from paddle.fluid import core


def actual(primal, cotangent, axis, keep_dim):
    core.set_prim_eager_enabled(False)
    x = paddle.to_tensor(primal, dtype='float32', stop_gradient=False)
    v = paddle.to_tensor(cotangent, dtype='float32', stop_gradient=False)
    y = paddle.sum(x, axis=axis, keepdim=keep_dim)
    x_cotangent = paddle.grad(y, x, v, create_graph=True, retain_graph=True)
    return x_cotangent[0]


def desired(primal, cotangent, axis, keep_dim):
    core.set_prim_eager_enabled(True)
    x = paddle.to_tensor(primal, dtype='float32', stop_gradient=False)
    v = paddle.to_tensor(cotangent, dtype='float32', stop_gradient=False)
    y = paddle.sum(x, axis=axis, keepdim=keep_dim)
    x_cotangent = paddle.grad(y, x, v, create_graph=True, retain_graph=True)
    return x_cotangent[0]


class TestSumGradComp(unittest.TestCase):
    def test_sum_grad_comp_1(self):
        self.primal = np.random.rand(10, 10)
        self.cotangent = np.array(np.random.rand())
        paddle.disable_static()

        np.testing.assert_allclose(
            actual=actual(self.primal, self.cotangent, [], False),
            desired=desired(self.primal, self.cotangent, [], False),
            rtol=1e-6,
            atol=0,
        )

    def test_sum_grad_comp_2(self):
        self.primal = np.random.rand(4, 3, 2)
        self.cotangent = np.random.rand(4, 2)
        paddle.disable_static()

        np.testing.assert_allclose(
            actual=actual(self.primal, self.cotangent, 1, False),
            desired=desired(self.primal, self.cotangent, 1, False),
            rtol=1e-6,
            atol=0,
        )

    def test_sum_grad_comp_3(self):
        self.primal = np.random.rand(4, 3, 2)
        self.cotangent = np.random.rand(4, 1, 2)
        paddle.disable_static()

        np.testing.assert_allclose(
            actual=actual(self.primal, self.cotangent, 1, True),
            desired=desired(self.primal, self.cotangent, 1, True),
            rtol=1e-6,
            atol=0,
        )

    def test_sum_grad_comp_4(self):
        self.primal = np.random.rand(4, 3, 2, 5)
        self.cotangent = np.random.rand(4, 1, 2, 1)
        paddle.disable_static()

        np.testing.assert_allclose(
            actual=actual(self.primal, self.cotangent, [1, 3], True),
            desired=desired(self.primal, self.cotangent, [1, 3], True),
            rtol=1e-6,
            atol=0,
        )

    def test_sum_grad_comp_5(self):
        self.primal = np.random.rand(4, 3, 2, 5)
        self.cotangent = np.random.rand(4, 2)
        paddle.disable_static()

        np.testing.assert_allclose(
            actual=actual(self.primal, self.cotangent, [1, 3], False),
            desired=desired(self.primal, self.cotangent, [1, 3], False),
            rtol=1e-6,
            atol=0,
        )

    def test_sum_grad_comp_6(self):
        self.primal = np.random.rand(3, 2, 5)
        self.cotangent = np.random.rand(3, 1, 1)
        paddle.disable_static()

        np.testing.assert_allclose(
            actual=actual(self.primal, self.cotangent, [-2, -1], True),
            desired=desired(self.primal, self.cotangent, [-2, -1], True),
            rtol=1e-6,
            atol=0,
        )


if __name__ == '__main__':
    unittest.main()
