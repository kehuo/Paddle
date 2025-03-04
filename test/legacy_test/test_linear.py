# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
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
import paddle.nn.functional as F
from paddle import fluid
from paddle.fluid import core


class LinearTestCase(unittest.TestCase):
    def setUp(self):
        self.dtype = 'float32'
        self.input = np.ones((3, 1, 2)).astype(self.dtype)
        self.weight = np.ones((2, 2)).astype(self.dtype)
        self.bias = np.ones(2).astype(self.dtype)
        self.place = (
            paddle.CUDAPlace(0)
            if core.is_compiled_with_cuda()
            else paddle.CPUPlace()
        )

    def functional(self, place):
        paddle.disable_static(place)
        input = paddle.to_tensor(self.input)
        weight = paddle.to_tensor(self.weight)
        bias = paddle.to_tensor(self.bias)
        out = F.linear(input, weight, bias)
        return out.numpy()

    def paddle_nn_layer(self, place):
        paddle.disable_static(place)
        input = paddle.to_tensor(self.input)
        weight_attr = fluid.ParamAttr(
            name="linear_weight",
            learning_rate=1.0,
            trainable=False,
            regularizer=None,
            initializer=paddle.nn.initializer.Constant(value=1.0),
        )
        bias_attr = fluid.ParamAttr(
            name="linear_bias",
            learning_rate=1.0,
            trainable=False,
            regularizer=None,
            initializer=paddle.nn.initializer.Constant(value=1.0),
        )
        linear = paddle.nn.Linear(
            2, 2, weight_attr=weight_attr, bias_attr=bias_attr
        )
        y = linear(input)
        return y.numpy()

    def numpy_cal(self):
        res = np.matmul(self.input, self.weight) + self.bias
        return res

    def test_error(self, place=paddle.CPUPlace()):
        res_f = self.functional(place)
        res_nn = self.paddle_nn_layer(place)
        res_np = self.numpy_cal()
        np.testing.assert_array_almost_equal(res_f, res_nn)
        np.testing.assert_array_almost_equal(res_nn, res_np)

    def test_weight_init(self):
        if not paddle.is_compiled_with_cuda():
            return
        paddle.seed(100)
        linear = paddle.nn.Linear(
            2, 3, weight_attr=paddle.nn.initializer.Normal(0, 1.0)
        )
        paddle.nn.utils._stride_column(linear.weight)
        expect = [
            [1.4349908, -0.8099171, -2.64788],
            [-1.4981681, -1.1784115, -0.023253186],
        ]
        np.testing.assert_allclose(linear.weight.numpy(), expect, rtol=1e-05)

        linear = paddle.nn.Linear(2, 3)
        expect = [
            [0.73261100, 0.43836895, 0.07908206],
            [0.85075015, -1.04724526, 0.64371765],
        ]
        np.testing.assert_allclose(linear.weight.numpy(), expect, rtol=1e-05)


if __name__ == "__main__":
    unittest.main()
