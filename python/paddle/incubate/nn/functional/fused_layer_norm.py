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


import paddle
from paddle import _C_ops
from paddle.framework import LayerHelper, in_dynamic_mode


def fused_layer_norm(
    x,
    norm_weight,
    norm_bias,
    epsilon,
    residual_alpha=1.0,
    begin_norm_axis=1,
    bias=None,
    residual=None,
    quant_scale=-1,
    quant_round_type=0,
    quant_max_bound=0,
    quant_min_bound=0,
):
    r"""
    Apply Fused LayerNorm kernel. Also support LayerNorm(bias + residual_alpha * residual + x) fused pattern.

    when norm_weight and norm_bias is None, it return fused (bias + residual_alpha * residual + x)

    Args:
        x (Tensor): the input Tensor..
        norm_weight (Tensor): the weight Tensor to affine output.
        norm_bias (Tensor): the bias Tensor to affine output.
        epsilon (float): a small float number to avoid divide 0.
        residual_alpha (float): a scale factor for residual. default is 1.
        begin_norm_axis (int): the begin axis to normalize. default is 1.
        bias (optional|Tensor): the previous layers's bias to fused.
        residual (optional|Tensor): the residual input to fused.
        quant_scale (float): the quant scale.
        quant_round_type (float): the quant round type.
        quant_max_bound (float): the quant max bound to clip.
        quant_min_bound (float): the quant min bound to clip.


    Returns:
        Tensor: the output Tensor.

    Examples:
        .. code-block:: python

            # required: gpu
            import paddle

            paddle_x = paddle.cast(paddle.randn(shape=[32, 256]), dtype=paddle.float16)
            paddle_weight = paddle.cast(paddle.randn(shape=[256]), dtype=paddle.float32)
            paddle_bias = paddle.cast(paddle.randn(shape=[256]), dtype=paddle.float32)
            epsilon = 1e-6
            paddle_layernorm = paddle.incubate.nn.functional.fused_layer_norm(paddle_x, paddle_weight, paddle_bias, epsilon, 1)
    """

    if in_dynamic_mode():
        return _C_ops.fused_bias_residual_layernorm(
            x,
            bias,
            residual,
            norm_weight,
            norm_bias,
            epsilon,
            residual_alpha,
            begin_norm_axis,
            quant_scale,
            quant_round_type,
            quant_max_bound,
            quant_min_bound,
        )

    helper = LayerHelper('fused_layernorm', **locals())
    out = None
    if quant_scale <= 0:
        out = helper.create_variable_for_type_inference(dtype=x.dtype)
    else:
        out = helper.create_variable_for_type_inference(dtype=paddle.int8)
    outputs_dict = {}
    outputs_dict['out'] = out
    outputs_dict['mean'] = helper.create_variable_for_type_inference(
        dtype=paddle.float32
    )
    outputs_dict['variance'] = helper.create_variable_for_type_inference(
        dtype=paddle.float32
    )

    residual_out = helper.create_variable_for_type_inference(dtype=x.dtype)
    outputs_dict['residual_out'] = residual_out

    inputs = {'x': x, 'norm_weight': norm_weight, 'norm_bias': norm_bias}
    if residual is not None:
        inputs['residual'] = residual
    if bias is not None:
        inputs['bias'] = bias

    helper.append_op(
        type='fused_bias_residual_layernorm',
        inputs=inputs,
        attrs={
            "epsilon": epsilon,
            "residual_alpha": residual_alpha,
            "begin_norm_axis": begin_norm_axis,
            "quant_scale": quant_scale,
            "quant_round_type": quant_round_type,
            "quant_max_bound": quant_max_bound,
            "quant_min_bound": quant_min_bound,
        },
        outputs=outputs_dict,
    )
    return out
